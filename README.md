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
- **Database:** Oracle Autonomous Database 23ai

---

## Setup Instructions

### 1. **Clone the Repository**
```bash
git clone https://github.com/yourusername/zenvault.git
cd zenvault
```

### 2. **Set Up the Environment**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the root directory with the following content:

```plaintext
username=your_db_username
password=your_db_password
DSN=your_db_dsn
```

---

### (Configre ansible playbook)
run this shell script to generate an inventory.ini file for your playbook.
- edit the contents of your .env variables.
```bash
export ANSIBLE_HOST=<ip address>
export ANSIBLE_SSH_USER=<host name>
export ANSIBLE_SSH_PRIVATE_KEY_FILE=<ssh_key_location>
```

```bash
source .env
```

```bash
bash generate_inventory.sh
```

### (Run playbook)

```bash
ansible-playbook -i inventory.ini deploy.yml
```

### 3. **Configure Oracle Instant Client**

```bash
nano ~/.bashrc

# Add the following lines:
export LD_LIBRARY_PATH=/home/ubuntu/instantclient_23_7:$LD_LIBRARY_PATH
export PATH=/home/ubuntu/instantclient_23_7:$PATH
export TNS_ADMIN="/home/ubuntu/<wallet_name>"

source ~/.bashrc
```

---

### 4. **Set Up IP Forwarding (Optional)**

```bash
sudo sysctl net.ipv4.ip_forward
sudo sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

---

### 5. **Configure Firewall**

```bash
sudo ufw status
sudo ufw enable
sudo ufw allow 5001/tcp
sudo ufw reload
```

---

### 6. **Run Flask App in Background**

Create a **systemd** service:

```bash
sudo nano /etc/systemd/system/flaskapp.service
```

Add the following configuration:

```plaintext
[Unit]
Description=Flask App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu
ExecStart=/usr/bin/bash -c 'source /home/ubuntu/.bashrc && /usr/bin/python3 /home/ubuntu/app.py'
Environment="FLASK_APP=app.py"
Environment="FLASK_RUN_HOST=0.0.0.0"
Environment="FLASK_RUN_PORT=5001"
Environment="LD_LIBRARY_PATH=/home/ubuntu/instantclient_23_7:$LD_LIBRARY_PATH"
Environment="PATH=/home/ubuntu/instantclient_23_7:$PATH"
Environment="TNS_ADMIN=/home/ubuntu/wallet_storagedb"
Restart=always
ExecStartPre=/bin/sleep 10

[Install]
WantedBy=multi-user.target
```

Reload and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl restart flaskapp
sudo systemctl status flaskapp
```

To stop the app:

```bash
sudo systemctl stop flaskapp
```

---

## Accessing the Application
Open a web browser and navigate to:

```plaintext
http://<your_server_ip>:5001
```

---

## File Management Endpoints
- **Upload File:** `/upload_page`
- **View Files:** `/file_page`
- **Download File:** `/download/<file_name>`
- **Delete File:** `/delete/<file_name>`
- **Preview File:** `/preview/<file_name>`

---

## Contribution
Feel free to open issues and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

---

## License
This project is licensed under the MIT License.

---

## Contact
For questions or support, please contact:

**Jeremy Hernandez**  
📧 [Jeremyhernandez.r@gmail.com](mailto:Jeremyhernandez.r@gmail.com)  
📍 Austin, TX 
