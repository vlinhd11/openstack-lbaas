URL=http://localhost:8181/loadbalancers
curl -X PUT -H "Content-Type: application/json" -d@updateNodeCommand $URL/$1/nodes/$2
