resource "oci_database_autonomous_database" "autonomous_database" { 
    compartment_id = var.compartment_ocid 
    db_name = "StorageDB" display_name = "StorageDB" 
    admin_password = var.admin_password 
    cpu_core_count = 1 data_storage_size_in_gb = 10 
    db_workload = "OLTP" 
    is_free_tier = true 
    db_version = "23ai" 
}