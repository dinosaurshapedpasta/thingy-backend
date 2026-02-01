import asyncio
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import logging
import os
import httpx

from sqlalchemy.orm import Session

from app.database import crud, models
from app.schemas import UserRead

logger = logging.getLogger(__name__)

# API Configuration
# Get API key from environment variable
# Sign up for free at: https://openrouteservice.org/dev/#/signup
OPENROUTE_API_KEY = os.getenv("OPENROUTE_API_KEY", "")
OPENROUTE_BASE_URL = "https://api.openrouteservice.org/v2"


class AuctionManager:
    """
    Manages the auction process for pickup requests.

    Workflow:
    1. Start auction when pickup request is created
    2. Wait 60 seconds for volunteer responses
    3. Collect GPS locations from responses
    4. Calculate distance/time matrix using Maps API
    5. Apply adjustments for capacity and karma
    6. Pass to routing algorithm
    7. Dispatch routes to selected volunteers
    """

    def __init__(self):
        # Store active auctions: {request_id: auction_data}
        self.active_auctions: Dict[str, dict] = {}

    async def start_auction(
        self,
        pickup_request_id: str,
        pickup_point_id: str,
        db: Session
    ):
        """
        Start an auction for a pickup request.

        Args:
            pickup_request_id: The ID of the pickup request
            pickup_point_id: The ID of the pickup point
            db: Database session
        """
        logger.info(f"Starting auction for pickup request {pickup_request_id}")

        # Initialize auction data
        auction_data = {
            "request_id": pickup_request_id,
            "pickup_point_id": pickup_point_id,
            "start_time": datetime.now(),
            "responses": [],
            "status": "waiting"
        }
        self.active_auctions[pickup_request_id] = auction_data

        # Broadcast to all volunteers (this would be handled by your notification system)
        await self._broadcast_to_volunteers(pickup_request_id, pickup_point_id)

        # Wait 60 seconds for responses
        await asyncio.sleep(60)

        # Process responses
        await self._process_responses(pickup_request_id, db)

    async def _broadcast_to_volunteers(self, request_id: str, pickup_point_id: str):
        """
        Broadcast pickup request to all volunteers.

        This would integrate with your notification system (WebSocket, push notifications, etc.)
        For now, this is a placeholder.
        """
        logger.info(f"Broadcasting pickup request {request_id} to all volunteers")
        # TODO: Implement actual notification system
        # This could be:
        # - WebSocket broadcast
        # - Push notifications
        # - SMS/Email
        pass

    async def _process_responses(self, request_id: str, db: Session):
        """
        Process all responses received during the 60-second window.
        """
        logger.info(f"Processing responses for pickup request {request_id}")

        auction_data = self.active_auctions.get(request_id)
        if not auction_data:
            logger.error(f"No auction data found for request {request_id}")
            return

        auction_data["status"] = "processing"

        # Get all responses from the database
        responses = crud.get_pickup_request_responses(db, request_id)

        # Filter only accepted responses (result == 1)
        accepted_volunteers = [r for r in responses if r.result == 1]

        if not accepted_volunteers:
            logger.info(f"No volunteers accepted pickup request {request_id}")
            auction_data["status"] = "failed_no_volunteers"
            return

        logger.info(f"Found {len(accepted_volunteers)} volunteers for request {request_id}")

        # Get pickup point location
        pickup_point = crud.get_pickup_point(db, auction_data["pickup_point_id"])
        if not pickup_point:
            logger.error(f"Pickup point {auction_data['pickup_point_id']} not found")
            auction_data["status"] = "failed_no_pickup_point"
            return

        # Get volunteer details including their location and capacity
        volunteer_data = []
        for response in accepted_volunteers:
            user = crud.get_user(db, response.userID)
            if user:
                volunteer_data.append({
                    "user_id": user.id,
                    "karma": user.karma,
                    "max_volume": user.maxVolume,
                    "location": response.location  # GPS location from response
                })

        # Calculate distance/time matrix
        adjacency_matrix = await self._calculate_adjacency_matrix(
            volunteer_data,
            pickup_point,
            db
        )

        # Call routing algorithm
        routes = await self._calculate_routes(
            adjacency_matrix,
            volunteer_data,
            pickup_point
        )

        # Dispatch routes to volunteers
        await self._dispatch_routes(routes, db)

        # Store results
        auction_data["routes"] = routes
        auction_data["status"] = "completed"
        logger.info(f"Completed auction for pickup request {request_id}")

    async def _calculate_adjacency_matrix(
        self,
        volunteers: List[dict],
        pickup_point: models.PickupPoint,
        db: Session
    ) -> List[List[float]]:
        """
        Calculate adjacency matrix with adjustments for capacity and karma.

        The matrix represents the "cost" or "weight" for each volunteer to handle the pickup.
        Lower values are better.

        Adjustments:
        - Distance/time to pickup point (from Maps API)
        - Available capacity of volunteer
        - Karma score (higher karma = lower cost)
        """
        logger.info(f"Calculating adjacency matrix for {len(volunteers)} volunteers")

        matrix = []

        # Get all drop-off points for the full matrix
        # TODO: Determine which drop-off points are relevant for this pickup
        # For now, we'll just calculate distance to pickup point

        for volunteer in volunteers:
            row = []

            # Calculate base cost (distance/time to pickup point)
            base_cost = await self._get_travel_time(
                volunteer.get("location"),
                pickup_point.location
            )

            # Apply capacity adjustment
            # Volunteers with more capacity get a bonus (lower cost)
            capacity_factor = 1.0 / (1.0 + volunteer["max_volume"] / 100.0)

            # Apply karma adjustment
            # Higher karma = lower cost
            karma_factor = 1.0 / (1.0 + volunteer["karma"] / 100.0)

            # Calculate final cost
            adjusted_cost = base_cost * capacity_factor * karma_factor

            row.append(adjusted_cost)
            matrix.append(row)

        return matrix

    async def _get_travel_time(
        self,
        origin: str | None,
        destination: str
    ) -> float:
        """
        Get travel time between two locations using OpenRouteService API.

        Location format: "lat,lon" e.g. "51.5074,-0.1278"

        Returns:
            Travel time in minutes
        """
        if not origin:
            # If no GPS location provided, use a high default cost
            logger.warning("No origin location provided, using default high cost")
            return 999.0

        if not OPENROUTE_API_KEY:
            logger.error("OPENROUTE_API_KEY not set, using fallback cost")
            return 50.0  # Fallback value

        try:
            # Parse lat,lon strings
            origin_lat, origin_lon = map(float, origin.split(","))
            dest_lat, dest_lon = map(float, destination.split(","))

            # OpenRouteService expects [lon, lat] format (note the order!)
            locations = [
                [origin_lon, origin_lat],
                [dest_lon, dest_lat]
            ]

            # Call OpenRouteService Matrix API
            url = f"{OPENROUTE_BASE_URL}/matrix/driving-car"
            headers = {
                "Authorization": OPENROUTE_API_KEY,
                "Content-Type": "application/json"
            }
            payload = {
                "locations": locations,
                "metrics": ["duration"],  # Get duration in seconds
                "units": "m"  # meters for distances
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

                # Extract duration from origin (0) to destination (1)
                # Duration is in seconds, convert to minutes
                duration_seconds = data["durations"][0][1]
                duration_minutes = duration_seconds / 60.0

                logger.info(
                    f"Travel time from {origin} to {destination}: "
                    f"{duration_minutes:.1f} minutes"
                )
                return duration_minutes

        except ValueError as e:
            logger.error(f"Invalid location format: {e}")
            return 999.0
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from OpenRouteService: {e.response.status_code}")
            if e.response.status_code == 401:
                logger.error("Invalid API key. Get one at https://openrouteservice.org/dev/#/signup")
            return 999.0
        except httpx.RequestError as e:
            logger.error(f"Network error calling OpenRouteService: {e}")
            return 999.0
        except Exception as e:
            logger.error(f"Unexpected error getting travel time: {e}")
            return 999.0

    async def _calculate_routes(
        self,
        adjacency_matrix: List[List[float]],
        volunteers: List[dict],
        pickup_point: models.PickupPoint
    ) -> List[dict]:
        """
        Calculate optimal routes using the routing algorithm.

        For now, this selects the volunteer with the LOWEST cost (best match).
        Lower cost = closer distance + higher karma + more capacity.

        Returns:
            List of route assignments: [{"user_id": str, "cost": float, "route": List[str]}]
        """
        logger.info("Calculating optimal routes")

        if not volunteers or not adjacency_matrix:
            logger.warning("No volunteers or empty adjacency matrix")
            return []

        # Find volunteer with minimum cost (best match)
        # Each row in adjacency_matrix corresponds to one volunteer
        min_cost = float('inf')
        best_volunteer_idx = -1

        for idx, row in enumerate(adjacency_matrix):
            # For single pickup, we just have one cost per volunteer
            cost = row[0] if row else float('inf')

            logger.info(
                f"Volunteer {volunteers[idx]['user_id']} "
                f"(karma: {volunteers[idx]['karma']}, "
                f"capacity: {volunteers[idx]['max_volume']}L) "
                f"-> Cost: {cost:.2f}"
            )

            if cost < min_cost:
                min_cost = cost
                best_volunteer_idx = idx

        if best_volunteer_idx == -1:
            logger.error("Could not find valid volunteer")
            return []

        selected_volunteer = volunteers[best_volunteer_idx]

        logger.info(
            f"✓ SELECTED: {selected_volunteer['user_id']} with cost {min_cost:.2f}"
        )

        # TODO: Integrate with actual routing algorithm for complex multi-pickup routes
        # For now, return simple single-pickup route
        return [{
            "user_id": selected_volunteer["user_id"],
            "cost": min_cost,
            "route": [pickup_point.id],  # In reality, would include dropoff points
            "volunteer_details": {
                "karma": selected_volunteer["karma"],
                "capacity": selected_volunteer["max_volume"]
            }
        }]

    async def _dispatch_routes(self, routes: List[dict], db: Session):
        """
        Send route assignments to selected volunteers.

        This would integrate with your notification system.
        """
        logger.info(f"Dispatching routes to {len(routes)} volunteers")

        for route in routes:
            user_id = route["user_id"]
            route_details = route["route"]

            # TODO: Send notification to volunteer with route details
            # This could be:
            # - WebSocket message
            # - Push notification
            # - SMS/Email
            # - Update in database for volunteer to poll

            logger.info(f"Dispatched route to volunteer {user_id}: {route_details}")

    def add_response(
        self,
        request_id: str,
        user_id: str,
        accepted: bool,
        gps_location: str | None = None
    ):
        """
        Add a volunteer response to an active auction.

        This is called when a volunteer accepts/denies a pickup request.
        """
        auction_data = self.active_auctions.get(request_id)
        if not auction_data:
            logger.warning(f"No active auction for request {request_id}")
            return False

        if auction_data["status"] != "waiting":
            logger.warning(f"Auction {request_id} is not in waiting state")
            return False

        auction_data["responses"].append({
            "user_id": user_id,
            "accepted": accepted,
            "gps_location": gps_location,
            "timestamp": datetime.now()
        })

        return True


# Global auction manager instance
auction_manager = AuctionManager()


async def handle_pickup_request(
    pickup_request_id: str,
    pickup_point_id: str,
    db: Session
):
    """
    Handle a new pickup request by starting an auction.

    This function should be called when a POST to /pickuprequests/ is received.
    """
    await auction_manager.start_auction(
        pickup_request_id,
        pickup_point_id,
        db
    )
