TERRAFORM_DIR = Infrastructure
ANSIBLE_DIR = Infrastructure
INVENTORY_FILE = $(ANSIBLE_DIR)/inventory.ini

all: infra wait-for-hosts configure

infra:
	cd $(TERRAFORM_DIR) && terraform init
	cd $(TERRAFORM_DIR) && terraform apply -auto-approve

wait-for-hosts:
	ansible all -i $(INVENTORY_FILE) -m wait_for_connection -a "timeout=300" --ssh-extra-args="-o StrictHostKeyChecking=no"

configure:
	ansible-playbook -i $(INVENTORY_FILE) $(ANSIBLE_DIR)/flask_server.yml
	ansible-playbook -i $(INVENTORY_FILE) $(ANSIBLE_DIR)/middleware-playbook.yml

clean:
	cd $(TERRAFORM_DIR) && terraform destroy -auto-approve
	rm -f $(INVENTORY_FILE)
	rm -f $(ANSIBLE_DIR)/group_vars/middleware.yml

middleware:
	ansible-playbook -i $(INVENTORY_FILE) $(ANSIBLE_DIR)/middleware-playbook.yml

flask:
	ansible-playbook -i $(INVENTORY_FILE) $(ANSIBLE_DIR)/flask_server.yml
