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

variable "instance_image_ocid" { 
    type = map(string) 
    // ubuntu image
    default = { 
        "us-ashburn-1" = "ocid1.image.oc1.iad.aaaaaaaadp3lalzonttesoe52qotckqmjth5qeow2wmiaiysykpo7ewqlnlq" 
    } 
}

variable "bucket_name" { 
    description = "Name of the OCI Object Storage bucket" 
    type = string 
    default = "zenvault-bucket-storage" 
}