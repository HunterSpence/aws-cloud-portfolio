.PHONY: deploy test local-invoke logs clean build validate

STACK_NAME   ?= eventstream
REGION       ?= us-east-1
ENV          ?= dev
TEMPLATE     := template.yaml

## deploy — Build and deploy the SAM stack
deploy: validate
	sam build --template $(TEMPLATE)
	sam deploy \
		--stack-name $(STACK_NAME)-$(ENV) \
		--region $(REGION) \
		--resolve-s3 \
		--capabilities CAPABILITY_IAM \
		--parameter-overrides Environment=$(ENV) \
		--confirm-changeset \
		--no-fail-on-empty-changeset

## test — Run unit tests with pytest
test:
	python -m pytest tests/ -v --tb=short

## local-invoke — Invoke the ingest function locally with a sample event
local-invoke:
	sam build --template $(TEMPLATE)
	sam local invoke IngestFunction \
		--event events/sample_event.json \
		--region $(REGION)

## logs — Tail CloudWatch logs for a function (usage: make logs FN=IngestFunction)
FN ?= IngestFunction
logs:
	sam logs --name $(FN) --stack-name $(STACK_NAME)-$(ENV) --region $(REGION) --tail

## validate — Validate the SAM template
validate:
	sam validate --template $(TEMPLATE) --region $(REGION)

## clean — Remove build artifacts
clean:
	rm -rf .aws-sam/
