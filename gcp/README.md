# GCP deployment

VM1: api-gateway + external IP
VM2: user-service + user MySQL
VM3: product-service + product MySQL
VM4: cart-order-service + order MySQL

Only VM1 should be reachable from the internet.

For GCP:
VM1 environment:
USER_SERVICE_URL=http://VM2_PRIVATE_IP:5001
PRODUCT_SERVICE_URL=http://VM3_PRIVATE_IP:5002
CART_ORDER_SERVICE_URL=http://VM4_PRIVATE_IP:5003

VM4 environment:
USER_SERVICE_URL=http://VM2_PRIVATE_IP:5001
PRODUCT_SERVICE_URL=http://VM3_PRIVATE_IP:5002

Keep MySQL port 3306 private. Backend ports 5001-5003 should only allow the required private VM sources.

The local docker-compose.yml is for testing all services on one machine. For the actual assignment, split the service/database pairs across four VMs.
