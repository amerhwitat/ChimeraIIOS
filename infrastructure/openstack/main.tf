terraform {
  required_version = ">= 1.6.0"
  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = ">= 1.54.0"
    }
  }
}

provider "openstack" {}

variable "image_id" { type = string }
variable "flavor_id" { type = string }
variable "network_id" { type = string }
variable "name" { type = string, default = "chimera-ii-os" }

resource "openstack_compute_instance_v2" "chimera" {
  name        = var.name
  image_id    = var.image_id
  flavor_id   = var.flavor_id
  network { uuid = var.network_id }
  stop_before_destroy = true
}

output "instance_id" { value = openstack_compute_instance_v2.chimera.id }
output "instance_name" { value = openstack_compute_instance_v2.chimera.name }
