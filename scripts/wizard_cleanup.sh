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

BLA::play_loading_animation_loop() {
    while true; do
        for frame in "${BLA_active_loading_animation[@]}"; do
            printf "\r%s" "${frame}"
            sleep "${BLA_loading_animation_frame_interval}"
        done
    done
}

BLA::start_loading_animation() {
    BLA_active_loading_animation=("$@")
    BLA::play_loading_animation_loop & BLA_loading_animation_pid="$!"
}

BLA::stop_loading_animation() {
    kill "${BLA_loading_animation_pid}" &> /dev/null
    printf "\n"
}

# Wizard messaging functions using colored text
wizard_says() {
    echo -e "\n🧙 Wizard: $1\n"
}

_print_yellow_bg() { echo -e "\033[0;103;30m$1\033[0m"; }
_print_blue_bg() { echo -e "\033[0;44;97m$1\033[0m"; }
_print_running() { echo -e " \033[1;30m - ${1}\033[0m"; }
_print_error() { echo -e "\033[1;31m*ERROR*: ${1}\033[0m"; }
_print_success() { echo -e "\033[1;32m*SUCCESS*: ${1}\033[0m"; }

# ASCII Art for Wizard
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

# Initial wizard introduction
clear
wizard_intro
wizard_says "Greetings, traveler! I am the Server Wizard, here to perform a mystical diagnostic on your server."

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
    local suspicious=$(ps -aux | grep -E 'kinsing|udiskssd|kdevtmpfsi|bash2|syshd|atdb' | grep -v 'grep')
    if [[ -n "$suspicious" ]]; then
        echo "True"
    else
        echo "False"
    fi
}

detect_encrypted_files() {
    find / -type f \( -name "*.psaux" -o -name "*.encryp" -o -name "*.locked" \) 2>/dev/null
}

# Diagnostic phase
wizard_says "Performing diagnostic checks on your server..."
BLA::start_loading_animation "${BLA_filling_bar[@]}"
malicious_files=$(detect_malicious_files)
has_suspicious_processes=$(detect_suspicious_processes)
encrypted_files=$(detect_encrypted_files)
BLA::stop_loading_animation

# Present diagnostic results and prompt the user
wizard_says "Diagnostic complete. Here is what has been discovered:"
[[ -n "$malicious_files" ]] && echo "- Malicious files detected: $malicious_files" || echo "- No malicious files detected."
[[ "$has_suspicious_processes" == "True" ]] && echo "- Suspicious processes detected." || echo "- No suspicious processes detected."
[[ -n "$encrypted_files" ]] && echo "- Encrypted files detected." || echo "- No encrypted files detected."

if [[ -z "$malicious_files" && "$has_suspicious_processes" == "False" && -z "$encrypted_files" ]]; then
    wizard_says "Your server is free from malicious entities detected by our checks. Keep the mystical realms safe by staying updated on CyberPanel forums."
    exit 0
fi

read -r -p "Do you wish to proceed with the necessary clean-up? (yes/no) " proceed  # shellcheck disable=SC2162
if [[ "$proceed" != "yes" ]]; then
    wizard_says "The purification ritual has been cancelled. Remain vigilant!"
    exit 0
fi

# Initiate cleansing based on diagnostic
[[ -n "$malicious_files" ]] && {
    wizard_says "Neutralizing detected malicious files..."
    BLA::start_loading_animation "${BLA_classic[@]}"
    for file in $malicious_files; do
        if rm -f "$file"; then
            echo "Removed $file"
        else
            echo "Failed to remove $file"
        fi
    done
    BLA::stop_loading_animation
}

[[ "$has_suspicious_processes" == "True" ]] && {
    wizard_says "Banish those conspiring processes..."
    BLA::start_loading_animation "${BLA_filling_bar[@]}"
    ps -aux | grep -E 'kinsing|udiskssd|kdevtmpfsi|bash2|syshd|atdb' | grep -v 'grep' | awk '{print $2}' | xargs -r kill -9 2>/dev/null
    BLA::stop_loading_animation
}

# New Kinsing-specific cleanup adapted to wizard theme
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

    # Start cleanup
    _print_yellow_bg "Proceeding to clean Kinsing malware from system"
    echo

    # Disable cron
    _print_yellow_bg "Step 1: Disable cron"
    systemctl stop cron
    [[ $? -eq 0 ]] && _print_success "Cron service stopped" || _print_error "Failed to stop cron service"
    echo

    # Delete malware files
    _print_yellow_bg "Step 2: Delete Malware Files"
    MALWARE_LOCATION=(
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

    for LOCATION in "${MALWARE_LOCATION[@]}"; do
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
    SUSPICIOUS_SERVICE=(
        bot
        system_d
        sshd-network-service
        network-monitor
    )

    for SERVICE in "${SUSPICIOUS_SERVICE[@]}"; do
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
    SUSPICIOUS_PROCESS=(
        kdevtmpfsi
        kinsing
        xmrig
        xmrigDaemon
        xmrigMiner
        xmrigMinerd
        xmrigMinerDaemon
        xmrigMinerServer
        xmrigMinerServerDaemon
        udiskssd
        bash2
        .network-setup
        syshd
        atdb
    )

    for PROCESS_GREP in "${SUSPICIOUS_PROCESS[@]}"; do
        mapfile -t PIDS_TO_KILL < <(pgrep -f -- "$PROCESS_GREP" 2>/dev/null || true)
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
        rm -f /etc/ld.so.preload
        [[ $? -eq 0 ]] && _print_success "Deleted /etc/ld.so.preload" || _print_error "Failed to delete /etc/ld.so.preload"
    else
        _print_success "/etc/ld.so.preload not found"
    fi
    echo

    # Remove malicious cron jobs
    _print_yellow_bg "Step 6: Remove Malicious Cron Jobs"
    CRONTAB_FILES=(
        /var/spool/cron/crontabs/root
        /var/spool/cron/root
    )
    MALICIOUS_MATCH_CRON=(
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
    systemctl start cron
    [[ $? -eq 0 ]] && _print_success "Cron service started" || _print_error "Failed to start cron service"
    echo
}

[[ -n "$malicious_files" || "$has_suspicious_processes" == "True" ]] && cleanup_kinsing

[[ -n "$encrypted_files" ]] && {
    wizard_says "Attempting to decrypt the detected encrypted files..."
    BLA::start_loading_animation "${BLA_filling_bar[@]}"
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
    BLA::stop_loading_animation
}

# Final report
wizard_says "The following actions have been completed during the purification:"
[[ -n "$malicious_files" ]] && echo "- Removed malicious files."
[[ "$has_suspicious_processes" == "True" ]] && echo "- Terminated suspicious processes."
[[ -n "$malicious_files" || "$has_suspicious_processes" == "True" ]] && echo "- Executed Kinsing cleanup procedures."
[[ -n "$encrypted_files" ]] && echo "- Attempted file decryption for encrypted files."

wizard_says "The cleansing ritual is complete. Your server is now protected from the detected threats. Stay vigilant, traveler, and remember to keep informed through CyberPanel forums. Until we meet again, fare thee well!"
