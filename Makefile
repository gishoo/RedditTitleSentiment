# Directory paths
TERRAFORM_DIR = infrastructure
ANSIBLE_DIR = infrastructure
INVENTORY_FILE = $(ANSIBLE_DIR)/inventory.ini

# Default target: provision infra and run Ansible
all: infra wait-for-hosts configure

# Step 1: Run Terraform to provision infrastructure
infra:
	cd $(TERRAFORM_DIR) && terraform init
	cd $(TERRAFORM_DIR) && terraform apply -auto-approve

# Step 2: Wait for SSH to be available on all hosts
wait-for-hosts:
	ansible all -i $(INVENTORY_FILE) -m wait_for_connection -a "timeout=300" --ssh-extra-args="-o StrictHostKeyChecking=no"

# Step 3: Configure servers via Ansible
configure:
	ansible-playbook -i $(INVENTORY_FILE) $(ANSIBLE_DIR)/flask_server.yml
	ansible-playbook -i $(INVENTORY_FILE) $(ANSIBLE_DIR)/middleware-playbook.yml

# Step 4: Tear down infrastructure and clean up files
clean:
	cd $(TERRAFORM_DIR) && terraform destroy -auto-approve
	rm -f $(INVENTORY_FILE)
	rm -f $(ANSIBLE_DIR)/group_vars/middleware.yml

# Optional: Run only one playbook
middleware:
	ansible-playbook -i $(INVENTORY_FILE) $(ANSIBLE_DIR)/middleware-playbook.yml

flask:
	ansible-playbook -i $(INVENTORY_FILE) $(ANSIBLE_DIR)/flask_server.yml
