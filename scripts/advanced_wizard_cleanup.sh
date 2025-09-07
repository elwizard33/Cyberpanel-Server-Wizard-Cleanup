#!/bin/bash

# Loading animation frames
BLA_classic=(
    "|"
    "/"
    "-"
    "\\"
)

BLA_filling_bar=(
    "[          ]"
    "[#         ]"
    "[##        ]"
    "[###       ]"
    "[####      ]"
    "[#####     ]"
    "[######    ]"
    "[#######   ]"
    "[########  ]"
    "[######### ]"
    "[##########]"
)

# Animation control functions
BLA_active_loading_animation=()
BLA_loading_animation_frame_interval=0.1
BLA_loading_animation_pid=0

BLA_play_loading_animation_loop() {
    while true; do
        for frame in "${BLA_active_loading_animation[@]}"; do
            printf "\r%s" "${frame}"
            sleep "${BLA_loading_animation_frame_interval}"
        done
    done
}

BLA_start_loading_animation() {
    BLA_active_loading_animation=("$@")
    BLA_play_loading_animation_loop &
    BLA_loading_animation_pid="$!"
}

BLA_stop_loading_animation() {
    kill "${BLA_loading_animation_pid}" &> /dev/null
    printf "\n"
}


wizard_says() {
    echo -e "\n🧙 Wizard: $1\n"
}

_print_yellow_bg() {
    echo -e "\033[0;103;30m$1\033[0m"
}

_print_blue_bg() {
    echo -e "\033[0;44;97m$1\033[0m"
}

_print_running() {
    echo -e " \033[1;30m - ${1}\033[0m"
}

_print_error() {
    echo -e "\033[1;31m*ERROR*: ${1}\033[0m"
}

_print_success() {
    echo -e "\033[1;32m*SUCCESS*: ${1}\033[0m"
}

wizard_intro() {
    cat << "EOF"
                         _______   ___       ___       __   ___  ________  ________  ________  ________                              
            |\  ___ \ |\  \     |\  \     |\  \|\  \|\_____  \|\   __  \|\   __  \|\   ___ \                             
            \ \   __/|\ \  \    \ \  \    \ \  \ \  \\|___/  /\ \  \|\  \ \  \|\  \ \  \_|\ \                             
             \ \  \_|/_\ \  \    \ \  \  __\ \  \ \  \   /  / /\ \   __  \ \   _  _\ \  \ \\ \                             
              \ \  \_|\ \ \  \____\ \  \|\__\_\  \ \  \ /  /_/__\ \  \ \  \ \  \\  \\ \  \_\\ \                             
               \ \_______\ \_______\ \____________\ \__\\________\ \__\ \__\ \__\\ _\\ \_______\                            
                \|_______|\|_______|\|____________|\|__|\|_______|\|__|\|__|\|__|\|__|\|_______|
EOF
}

clear
wizard_intro
wizard_says "Greetings, traveler! I am the Server Wizard, here to perform a mystical diagnostic on your server."

# Ensure script is run by root/sudo
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

# Function to prompt user for confirmation
prompt_user() {
    # shellcheck disable=SC2162
    read -r -p "$1 (yes/no) " response
    if [[ "$response" != "yes" ]]; then
        return 1
    fi
    return 0
}

# Diagnostic functions
detect_malicious_files() {
    local files=(
        "/etc/data/kinsing"
        "/etc/kinsing"
        "/tmp/kdevtmpfsi"
        "/usr/lib/secure"
        "/usr/lib/secure/udiskssd"
        "/usr/bin/network-setup.sh"
        "/usr/.sshd-network-service.sh"
        "/usr/.network-setup"
        "/usr/.network-watchdog.sh"
        "/etc/data/libsystem.so"
        "/dev/shm/kdevtmpfsi"
    )
    local found_files=()
    for file in "${files[@]}"; do
        if [ -e "$file" ]; then
            found_files+=("$file")
        fi
    done
    echo "${found_files[@]}"
}

detect_suspicious_processes() {
    if pgrep -fa 'kinsing|udiskssd|kdevtmpfsi|bash2|syshd|atdb' >/dev/null 2>&1; then
        echo "True"
    else
        echo "False"
    fi
}

detect_encrypted_files() {
    find / -type f \( -name "*.psaux" -o -name "*.encryp" -o -name "*.locked" \) 2>/dev/null
}

check_for_malicious_users() {
    local suspicious_users=()
    local known_users=("root" "admin" "ubuntu")
    local log_file="/var/log/suspicious_users.log"

    # Ensure the log file exists
    touch "$log_file"

    # Check for unexpected sudo users
    local sudo_users joined_known_users
    sudo_users=$(getent group sudo | awk -F: '{print $4}' | tr ',' '\n')
    joined_known_users=" ${known_users[*]} "
    for user in $sudo_users; do
        if [[ $joined_known_users != *" $user "* ]]; then
            suspicious_users+=("$user")
        fi
    done

    # Check for malformed usernames (e.g., usernames with symbols)
    local all_users
    all_users=$(getent passwd | cut -d: -f1)
    for user in $all_users; do
        if [[ "$user" =~ [^a-zA-Z0-9._-] ]]; then
            suspicious_users+=("$user")
        fi
    done

    # Identify users with unexpected UID ranges
    while IFS=: read -r username _ _ uid _; do
        if [[ "$uid" -ge 1000 && "$uid" -le 65533 ]]; then
            if [[ $joined_known_users != *" $username "* ]]; then
                suspicious_users+=("$username")
            fi
        fi
    done < <(getent passwd)

    # Verify suspicious users with the user and log responses
    if ((${#suspicious_users[@]})); then
        echo "Detected possible malicious users:"
    fi
    for user in "${suspicious_users[@]}"; do
        # shellcheck disable=SC2162
        read -r -p "Do you recognize the user '$user'? (yes/no) " response
        log_message="User '$user': $response"
        echo "$log_message" | tee -a "$log_file"

        if [[ "$response" == "no" ]]; then
            echo "User '$user' flagged as potentially malicious."
            # Additional handling logic could be included here, e.g., notification, disabling user
        else
            echo "User '$user' recognized by the administrator."
        fi
    done

    echo "${suspicious_users[@]}"
}

check_for_unauthorized_keys() {
    local key_files=( "/root/.ssh/authorized_keys" )
    local unauthorized_keys=()
    local log_file="/var/log/unauthorized_keys.log"

    # Ensure the log file exists
    touch "$log_file"

    for file in "${key_files[@]}"; do
        if [[ -f "$file" ]]; then
            echo "Checking SSH keys in $file:"
        while IFS= read -r key; do
                if [[ -n "$key" ]]; then
                    echo "Key found: $key"
            # shellcheck disable=SC2162
            read -r -p "Do you recognize this SSH key? (yes/no) " response
                    log_message="Key: $key - Recognized: $response"
                    echo "$log_message" | tee -a "$log_file"

                    if [[ "$response" == "no" ]]; then
                        unauthorized_keys+=("$key")
                    fi
                fi
            done < "$file"
        else
            echo "No authorized_keys file found at $file."
        fi
    done

    if (( ${#unauthorized_keys[@]} )); then
        echo "Unauthorized keys detected:" 
        for k in "${unauthorized_keys[@]}"; do
            echo "  - $k"
        done
        echo "Consider removing these keys if they're not recognized by administrators."
    else
        echo "All SSH keys verified as recognized."
    fi
}



# Diagnostic phase
wizard_says "Performing diagnostic checks on your server..."
BLA_start_loading_animation "${BLA_filling_bar[@]}"
malicious_files=$(detect_malicious_files)
has_suspicious_processes=$(detect_suspicious_processes)
encrypted_files=$(detect_encrypted_files)
mapfile -t suspicious_users_array < <(check_for_malicious_users)
mapfile -t unauthorized_keys_array < <(check_for_unauthorized_keys)
BLA_stop_loading_animation

# Diagnostic results display
wizard_says "Diagnostic complete. Here is what has been discovered:"

[[ -n "$malicious_files" ]] && echo "- Malicious files detected: $malicious_files" || echo "- No malicious files detected."
[[ "$has_suspicious_processes" == "True" ]] && echo "- Suspicious processes detected." || echo "- No suspicious processes detected."
[[ -n "$encrypted_files" ]] && echo "- Encrypted files detected." || echo "- No encrypted files detected."
if ((${#suspicious_users_array[@]})); then
    printf -- '- Suspicious users detected: %s\n' "${suspicious_users_array[*]}"
else
    echo "- No suspicious users detected."
fi
if ((${#unauthorized_keys_array[@]})); then
    echo "- Unauthorized SSH keys detected."
else
    echo "- No unauthorized SSH keys detected."
fi

# Protect if no threats are found
# If nothing was found, exit early
if [[ -z "$malicious_files" && "$has_suspicious_processes" == "False" && -z "$encrypted_files" && ${#suspicious_users_array[@]} -eq 0 && ${#unauthorized_keys_array[@]} -eq 0 ]]; then
    wizard_says "Your server is free from malicious entities detected by our checks. Keep the mystical realms safe by staying updated on CyberPanel forums."
    exit 0
fi

if ! prompt_user "Do you wish to proceed with the necessary clean-up?"; then
    wizard_says "The purification ritual has been cancelled. Remain vigilant!"
    exit 0
fi

# Initiate cleansing based on diagnostic
if [[ -n "$malicious_files" ]]; then
    wizard_says "Neutralizing detected malicious files..."
    if prompt_user "Remove malicious files?"; then
    BLA_start_loading_animation "${BLA_classic[@]}"
        for file in $malicious_files; do
            if rm -f "$file"; then
                echo "Removed $file"
            else
                echo "Failed to remove $file"
            fi
        done
    BLA_stop_loading_animation
    fi
fi

if [[ "$has_suspicious_processes" == "True" ]]; then
    wizard_says "Banish those conspiring processes..."
    if prompt_user "Terminate suspicious processes?"; then
    BLA_start_loading_animation "${BLA_filling_bar[@]}"
        # Use pgrep directly for process IDs
        mapfile -t _pids < <(pgrep -f 'kinsing|udiskssd|kdevtmpfsi|bash2|syshd|atdb' 2>/dev/null || true)
        if ((${#_pids[@]})); then
            kill -9 "${_pids[@]}" 2>/dev/null || true
        fi
    BLA_stop_loading_animation
    fi
fi

# Kinsing cleanup
cleanup_kinsing() {
    wizard_says "Executing additional spells to cleanse the system of Kinsing traces..."
    
    _print_yellow_bg "Check 1: Checking for running Kinsing malware..."
    if [[ $(_check_for_running_kinsing) ]]; then
        _print_error "Found Kinsing malware"
    else
        _print_success "No Kinsing malware found running"
    fi

    _print_yellow_bg "Check 2: Checking if /usr/local/CyberCP/databases/views.py is patched..."
    _check_patch
    echo

    prompt_user "Proceed with the Kinsing malware cleaning steps?"
    if prompt_user "Proceed with the Kinsing malware cleaning steps?"; then
    
        # Start cleanup
        _print_yellow_bg "Proceeding to clean Kinsing malware from system"
        echo

        # Disable cron
        _print_yellow_bg "Step 1: Disable cron"
        if systemctl stop cron; then
            _print_success "Cron service stopped"
        else
            _print_error "Failed to stop cron service"
        fi
        echo

        # Delete malware files
        _print_yellow_bg "Step 2: Delete Malware Files"
    local MALWARE_LOCATIONS=(
            /etc/data/kinsing
            /etc/kinsing
            /tmp/kdevtmpfsi
            /tmp/kinsing
            /var/tmp/kinsing
            /usr/lib/secure
            /usr/lib/secure/udiskssd
            /usr/bin/network-setup.sh
            /usr/.sshd-network-service.sh
            /usr/.network-setup
            /usr/.network-setup/config.json
            /usr/.network-setup/xmrig-*tar.gz
            /usr/.network-watchdog.sh
            /etc/data/libsystem.so
            /etc/data/kinsing
            /dev/shm/kdevtmpfsi
            /tmp/.ICEd-unix
            /var/tmp/.ICEd-unix
        )

        for LOCATION in "${MALWARE_LOCATIONS[@]}"; do
            if [ -f "$LOCATION" ]; then
                if rm -f "$LOCATION"; then
                    _print_success "Deleted $LOCATION"
                else
                    _print_error "Failed to delete $LOCATION"
                fi
            elif [ -d "$LOCATION" ]; then
                if rm -rf "$LOCATION"; then
                    _print_success "Deleted $LOCATION"
                else
                    _print_error "Failed to delete $LOCATION"
                fi
            else
                _print_running "$LOCATION not found"
            fi
        done
        echo

        # Remove suspicious services
        _print_yellow_bg "Step 3: Remove Suspicious Services"
    local SUSPICIOUS_SERVICES=(
            bot
            system_d
            sshd-network-service
            network-monitor
        )

        for SERVICE in "${SUSPICIOUS_SERVICES[@]}"; do
            if systemctl is-active --quiet "$SERVICE"; then
                _print_error "$SERVICE found"
                systemctl stop "$SERVICE"
                systemctl disable "$SERVICE"
                rm -f "/etc/systemd/system/$SERVICE.service"
            else
                _print_success "$SERVICE not found"
            fi
        done
        echo

        # Kill suspicious processes
        _print_yellow_bg "Step 4: Kill Suspicious Processes"
    local SUSPICIOUS_PROCESSES=(
            kdevtmpfsi
            kinsing
            xmrig
            xmrigDaemon
            xmrigMiner
            xmrigMinerd
            xmrigMinerDaemon
            xmrigMin...
        )
        
        for PROCESS_GREP in "${SUSPICIOUS_PROCESSES[@]}"; do
            mapfile -t PIDS_TO_KILL < <(pgrep -f -- "$PROCESS_GREP" 2>/dev/null || true)
            # Remove current script PID if present
            for i in "${!PIDS_TO_KILL[@]}"; do
                [[ ${PIDS_TO_KILL[$i]} -eq $$ ]] && unset 'PIDS_TO_KILL[$i]'
            done
            if [[ ${#PIDS_TO_KILL[@]} -eq 0 ]]; then
                _print_success "No $PROCESS_GREP found"
            else
                for PID in "${PIDS_TO_KILL[@]}"; do
                    kill -9 "$PID" 2>/dev/null || true
                done
            fi
        done
        echo

        # Unload pre-loaded libraries
        _print_yellow_bg "Step 5: Unload pre-loaded libraries"
        if [ -f /etc/ld.so.preload ]; then
            if rm -f /etc/ld.so.preload; then
                _print_success "Deleted /etc/ld.so.preload"
            else
                _print_error "Failed to delete /etc/ld.so.preload"
            fi
        else
            _print_success "/etc/ld.so.preload not found"
        fi
        echo
        
        # Remove malicious cron jobs
        _print_yellow_bg "Step 6: Remove Malicious Cron Jobs"
    local CRONTAB_FILES=(
            /var/spool/cron/crontabs/root
            /var/spool/cron/root
        )
    local MALICIOUS_MATCH_CRON=(
            kdevtmpfsi
            unk.sh
            atdb
            cp.sh
            p.sh
            wget
        )

        for CRON_FILE in "${CRONTAB_FILES[@]}"; do
            if [ -f "$CRON_FILE" ]; then
                for MATCH in "${MALICIOUS_MATCH_CRON[@]}"; do
                    if grep -q -- "$MATCH" "$CRON_FILE"; then
                        sed -i "/$MATCH/d" "$CRON_FILE"
                    fi
                done
            else
                _print_running "$CRON_FILE not found"
            fi
        done
        
        # Start cron
        _print_yellow_bg "Step 8: Start Cron"
        if systemctl start cron; then
            _print_success "Cron service started"
        else
            _print_error "Failed to start cron service"
        fi
        echo
    fi
}

if [[ -n "$malicious_files" || "$has_suspicious_processes" == "True" ]]; then
    cleanup_kinsing
fi

if [[ -n "$encrypted_files" ]]; then
    wizard_says "Attempting to decrypt the detected encrypted files..."
    if prompt_user "Proceed with decryption attempts?"; then
    BLA_start_loading_animation "${BLA_filling_bar[@]}"
        for enc_file in $encrypted_files; do
            case "$enc_file" in
                *.psaux)
                    curl -o 1-decrypt.sh https://gist.githubusercontent.com/gboddin/d78823245b518edd54bfc2301c5f8882/raw/d947f181e3a1297506668e347cf0dec24b7e92d1/1-decrypt.sh
                    bash 1-decrypt.sh "$enc_file"
                    ;;
                *.encryp)
                    curl -o encryp_dec.out https://github.com/v0idxyz/babukencrypdecrytor/raw/c71b409cf35469bb3ee0ad593ad48c9465890959/encryp_dec.out
                    chmod +x encryp_dec.out
                    ./encryp_dec.out "$enc_file"
                    ;;
            esac
        done
    BLA_stop_loading_animation
    fi
fi

# Final report and reminders
wizard_says "The following actions have been completed during the purification:"
[[ -n "$malicious_files" ]] && echo "- Removed malicious files."
[[ "$has_suspicious_processes" == "True" ]] && echo "- Terminated suspicious processes."
[[ -n "$malicious_files" || "$has_suspicious_processes" == "True" ]] && echo "- Executed Kinsing cleanup procedures."
[[ -n "$encrypted_files" ]] && echo "- Attempted file decryption for encrypted files."

wizard_says "The cleansing ritual is complete. Your server is now protected from the detected threats. Here are a few additional steps to consider:"
echo "- Take a snapshot for backup if issues persist."
echo "- Secure your firewall by only allowing connections from trusted IPs."
echo "- Change all relevant passwords, including root and service-specific passwords."
echo "- Implement methods for regular monitoring of server health."

wizard_says "Stay vigilant, traveler, and keep informed through CyberPanel forums. Until we meet again, fare thee well!"
