# CyberPanel Server Wizard Cleanup Scripts

### Overview

These scripts are designed to help identify and clean potential malware and ransomware infections on CyberPanel servers. There are two versions available: the Basic version and the Advanced version. Both perform diagnostics to detect malicious files, suspicious processes, and encrypted files, followed by appropriate cleanup and decryption processes.

### Features of Both Scripts

- **Automated Diagnostics**: Identify malicious files, suspicious processes, and encrypted files.
- **Cleanup of Malicious Artifacts**: Remove detected malicious files and terminate suspicious processes.
- **Ransomware Decryption**: Attempt to decrypt files encrypted with known ransomware extensions.
- **Wizard-Themed Interface**: Engage users with an intuitive, themed experience guiding them through the cleanup process.

### Advanced Version Features

- **User Interaction**: Prompts users for confirmation before executing critical cleanup tasks, ensuring control over actions.
- **Detailed User and Key Auditing**: Scans for suspicious users and SSH keys, providing a detailed report of potential security threats.
- **Enhanced Security Recommendations**: Offers additional security measures to consider after cleanup.
- **Ensures Root Privileges**: Confirms the script is run with appropriate permissions for effective operation.

### Detailed Differences Between Versions

- **User Confirmation**: 
  - *Basic*: Executes tasks with minimal user input, focusing on efficiency.
  - *Advanced*: Interactively prompts the user for confirmations at critical steps to ensure actions align with user intent.
  
- **Malicious User and Key Checks**: 
  - *Basic*: Does not check for suspicious users or SSH keys.
  - *Advanced*: Includes comprehensive checks for unauthorized users and unexpected SSH keys, asking the user for validation.
  
- **Security Recommendations Post-Cleanup**:
  - *Basic*: Focuses on the immediate cleanup.
  - *Advanced*: Provides additional security tips post-cleanup, such as password changes and firewall adjustments.

### Decrypting Scripts

- **`.psaux` Files**: Decrypted using [1-decrypt.sh](https://gist.github.com/gboddin/d78823245b518edd54bfc2301c5f8882/raw/d947f181e3a1297506668e347cf0dec24b7e92d1/1-decrypt.sh).
- **`.encryp` Files**: Decrypted using [encryp_dec.out](https://github.com/v0idxyz/babukencrypdecrytor/raw/c71b409cf35469bb3ee0ad593ad48c9465890959/encryp_dec.out).

### Prerequisites

- Ensure you have `curl`, `wget`, and `bash` available on your system.
- **Take a Snapshot**: If you’re using a virtual machine, take a snapshot before you start to safeguard against unintended consequences.
- Follow cybersecurity best practices by backing up your data prior to running the scripts.

### Quick Start

You can directly download and execute the **Basic** version of the script using the following command:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberpanel-Server-Wizard-Cleanup/refs/heads/main/scripts/wizard_cleanup.sh)"
```

For the **Advanced** version, use this command:

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/elwizard33/Cyberpanel-Server-Wizard-Cleanup/refs/heads/main/scripts/advanced_wizard_cleanup.sh)"
```

### Support

If you do not feel comfortable running these scripts or need further assistance, you can contact me at mago@elwizard.net for paid support.

### Acknowledgments

- Thank you to [@usmannasir](https://github.com/usmannasir) for sharing the decryption scripts used in this cleanup process.

### Other Tools For Cleaning The Attack

- [ManagingWP CyberPanel RCE Auth Bypass](https://github.com/managingwp/cyberpanel-rce-auth-bypass)
- [ArrayIterator's Cleanup Gist](https://gist.github.com/ArrayIterator/ebd67a0b4862e6bfb5d021c9f9d8dcd3)
- [Yoyosan's Cleanup Gist](https://gist.github.com/yoyosan/5f88c1a023f006f952d7378bdc7bcf01)
- [NothingCtrl's First Cleanup Gist](https://gist.github.com/NothingCtrl/710a12db2acb01baf66e3b4572919743)
- [NothingCtrl's Second Cleanup Gist](https://gist.github.com/NothingCtrl/78a7a8f0b2c35ada80bf6d52ac4cfef0)
- [Crosstyan's Cleanup Gist](https://gist.github.com/crosstyan/93966e4ab9c85b038e85308df1c8b420)

### Disclaimer

These scripts are provided as-is, without any warranty or guarantee. Use them at your own risk. The author is not responsible for any harm or loss resulting from the use of these scripts. Always ensure your environments are backed up and secure before running any security scripts.

