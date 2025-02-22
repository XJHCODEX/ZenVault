/* 
--Activate Environment Files--
source env-vars.sh 
source .venv/bin/activate
--Important Commands--
terraform -help
*/

// Define variables for sensitive information like tenancy, user OCID, etc.
variable "tenancy_ocid" {}
variable "user_ocid" {}
variable "fingerprint" {}
variable "private_key_path" {}
variable "region" {}
variable "compartment_ocid" {}
variable "ssh_public_key" {}
variable "ssh_private_key" {}
variable "subnet_ocid" {}
variable "admin_password" {}

// Instance image OCID for the specific region (mapped by region name)
variable "instance_image_ocid"{
    type = map(string)

    default = {
        // Ubuntu image
        "us-ashburn-1" = "ocid1.image.oc1.iad.aaaaaaaadp3lalzonttesoe52qotckqmjth5qeow2wmiaiysykpo7ewqlnlq"
    }
}
// Configure the OCI provider using the provided variables
provider "oci" {
    tenancy_ocid = "${var.tenancy_ocid}"
    user_ocid = "${var.user_ocid}"
    fingerprint = "${var.fingerprint}"
    private_key_path = "${var.private_key_path}"
    region = "${var.region}"
}

// Data source to get availability domain details for the specified compartment
data "oci_identity_availability_domain" "ad" {
    compartment_id = "${var.tenancy_ocid}"
    ad_number = 1
}

// Data source to get the object storage namespace for OCI
data "oci_objectstorage_namespace" "ns" {}

// Output the namespace value from the object storage data source
output namespace {
    value = "${data.oci_objectstorage_namespace.ns.namespace}"
}

variable "bucket_name" {
  description = "Name of the OCI Object Storage bucket"
  type        = string
  default     = "zenvault-bucket-storage"
}

resource "oci_objectstorage_bucket" "storage_bucket" {
  compartment_id = var.compartment_ocid
  name           = var.bucket_name
  namespace      = data.oci_objectstorage_namespace.ns.namespace // Dynamically fetched
  storage_tier   = "Standard"  
  access_type    = "ObjectRead" // Allow public access
} 

/* Resource to create a block volume (200GB) in 
the specified availability domain and compartment */
resource "oci_core_volume" "block_volume"{
    availability_domain = "${data.oci_identity_availability_domain.ad.name}"
    compartment_id = "${var.compartment_ocid}"
    display_name = "ZenVaultBV"
    size_in_gbs = "50"
}

/* Resource to create a compute instance (VM.Standard.E2.1.Micro)
in the specified availability domain and subnet */
resource "oci_core_instance" "storage_server"{
    compartment_id      = "${var.compartment_ocid}"
    availability_domain = "${data.oci_identity_availability_domain.ad.name}"
    display_name        = "ZenVaultInstance"
    shape               = "VM.Standard.E2.1.Micro"
    create_vnic_details {
    subnet_id           = "${var.subnet_ocid}"
  }
    source_details {
        source_type = "image"
        source_id   = "${var.instance_image_ocid[var.region]}"
  }
    metadata = {
        ssh_authorized_keys = "${var.ssh_public_key}"
  }
}

resource "oci_database_autonomous_database" "autonomous_database" {
  compartment_id           = "${var.compartment_ocid}"
  db_name                  = "StorageDB"
  display_name             = "StorageDB"
  admin_password           = "$var.admin_password}"
  cpu_core_count           = 1 
  data_storage_size_in_gb  = 10
  db_workload              = "OLTP"
  is_free_tier             = true 
  db_version               = "23ai"  

}