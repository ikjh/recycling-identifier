  
WORKER_VERSION=1.3

build-work:
	docker build -f Dockerfile-worker -t worker-server:$(WORKER_VERSION) .

tag-work:
	docker tag worker-server:$(WORKER_VERSION) gcr.io/final-recycling-project/worker-server:$(WORKER_VERSION)

push-work:
	docker push gcr.io/final-recycling-project/worker-server:$(WORKER_VERSION)