# =============================================================================
# CloudForge — Makefile
# =============================================================================
# Usage:
#   make init          Initialize Terraform (download providers & modules)
#   make plan          Preview infrastructure changes
#   make apply         Apply infrastructure changes
#   make destroy       Tear down all infrastructure
#   make fmt           Format all .tf files
#   make validate      Validate Terraform configuration
#   make lint          fmt + validate in one step
#   make clean         Remove local Terraform cache
# =============================================================================

.PHONY: init plan apply destroy fmt validate lint clean

PLAN_FILE := tfplan

init:
	terraform init -upgrade

plan: fmt validate
	terraform plan -out=$(PLAN_FILE)

apply:
	@test -f $(PLAN_FILE) && terraform apply $(PLAN_FILE) || terraform apply

destroy:
	terraform destroy

fmt:
	terraform fmt -recursive

validate:
	terraform validate

lint: fmt validate

clean:
	rm -rf .terraform .terraform.lock.hcl $(PLAN_FILE)
