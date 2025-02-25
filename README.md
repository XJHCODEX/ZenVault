# ZenVault - Secure Cloud File Storage System

![ZenVault Logo](static/favicon.ico)

## Overview
**ZenVault** is a secure and scalable cloud-based file storage system built using **Flask** and **Oracle Cloud Infrastructure (OCI)**. It allows users to securely upload, store, and manage files with seamless access control and role-based permissions. The application supports a wide variety of file types, including documents, images, videos, and audio files.

---

## Features
- 🔒 **Secure File Uploads:** Supports a range of file types including PDFs, images, videos, and audio files.
- 🚀 **Scalable Infrastructure:** Built on **OCI**, leveraging **Autonomous Transaction Processing 23AI**, **VCN**, **Vault**, **REST API**, and **Object Storage**.
- 🎥 **Media Preview:** Supports in-browser media streaming with byte-range support.
- 📂 **File Management:** Download, delete, and preview files directly from the web interface.
- ⚡ **Automated Deployment:** Provisioned using **Ansible**, with automated startup using **systemd** service.

---

## Technology Stack
- **Backend:** Flask, cx_Oracle
- **Frontend:** HTML, CSS, Bootstrap, JavaScript
- **Cloud Infrastructure:** Oracle Cloud Infrastructure (OCI)
- **Automation:** Ansible
- **DevOps:** systemd for service management
- **Database:** Oracle Autonomous Database

---

## Setup Instructions

### 1. **Clone the Repository**
```bash
git clone https://github.com/yourusername/zenvault.git
cd zenvault
