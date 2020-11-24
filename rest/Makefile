LOG_VERSION=0.1
REST_VERSION=0.1

build-log:
	docker build -f Dockerfile-logs -t logs:$(LOG_VERSION) .

tag-log:
	docker tag logs:$(LOG_VERSION) gcr.io/final-recycling-project/logs:$(LOG_VERSION)

push-log:
	docker push gcr.io/final-recycling-project/logs:$(LOG_VERSION)

build-rest:
	docker build -f Dockerfile-rest -t rest-server:$(REST_VERSION) .

tag-rest:
	docker tag rest-server:$(REST_VERSION) gcr.io/final-recycling-project/rest-server:$(REST_VERSION)

push-rest:
	docker push gcr.io/final-recycling-project/rest-server:$(REST_VERSION)