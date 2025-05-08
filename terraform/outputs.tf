data "oci_objectstorage_namespace" "ns" {
}

// Output the namespace value from the object storage data source
output "namespace" {
  value = data.oci_objectstorage_namespace.ns.namespace
}