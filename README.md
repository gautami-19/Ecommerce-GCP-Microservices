# Ecommerce GCP Microservices

4-service ecommerce application using Python Flask + MySQL + Docker.

Services:
1. API Gateway
2. User Service + User DB
3. Product Service + Product DB
4. Cart/Order Service + Order DB

Local:
docker compose up --build

Open: http://localhost:5000

Stop:
docker compose down

Delete database volumes:
docker compose down -v

GCP target:
VM1 = API Gateway (external IP)
VM2 = User Service + User MySQL
VM3 = Product Service + Product MySQL
VM4 = Cart/Order Service + Order MySQL

Backend VMs should communicate using private IPs. Do not expose MySQL publicly.
