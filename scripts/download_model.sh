#!/bin/bash

# Script to download Ollama model with speed monitoring and resume capability
set -e

MODEL_NAME="CognitiveComputations/dolphin-mistral-nemo:latest"
MAX_ATTEMPTS=5
MIN_SPEED_MBPS=5  # 5 MB/s minimum speed
STALL_TIMEOUT=300  # 5 minutes (kept for compatibility)

echo "Starting model download: $MODEL_NAME"

# Function to monitor download speed
monitor_download() {
    local pid=$1
    local start_time=$(date +%s)
    local last_check_time=$start_time
    local last_size=0
    local stall_count=0
    
    echo "Monitoring download speed (minimum: ${MIN_SPEED_MBPS} MB/s)..."
    
    local start_time=$(date +%s)
    local max_duration=1800  # 30 minutes max
    
    while kill -0 $pid 2>/dev/null; do
        sleep 30  # Check every 30 seconds
        
        # Check if process is still running
        if ! kill -0 $pid 2>/dev/null; then
            echo "Download process completed"
            break
        fi
        
        # Check for timeout
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        if [ $elapsed -gt $max_duration ]; then
            echo "❌ Download timed out after ${max_duration} seconds"
            kill $pid 2>/dev/null || true
            return 1
        fi
        
        # Get current download size from ollama logs
        local current_size=0
        if [ -d "/root/.ollama/models" ]; then
            # Try to get size from model directory
            current_size=$(du -sb /root/.ollama/models 2>/dev/null | cut -f1 || echo "0")
        fi
        
        # Calculate speed if we have previous data
        if [ $last_size -gt 0 ] && [ $current_size -gt $last_size ]; then
            local time_diff=$(( $(date +%s) - last_check_time ))
            local size_diff=$(( current_size - last_size ))
            local speed_mbps=$(( (size_diff * 8) / (time_diff * 1000000) ))  # Convert to MB/s
            
            echo "Download speed: ${speed_mbps} MB/s (${current_size} bytes total)"
            
            # Check if speed is too slow
            if [ $speed_mbps -lt $MIN_SPEED_MBPS ]; then
                stall_count=$((stall_count + 1))
                echo "⚠️  Slow download detected (${speed_mbps} MB/s < ${MIN_SPEED_MBPS} MB/s) - stall count: ${stall_count}"
                
                if [ $stall_count -ge 3 ]; then
                    echo "❌ Download stalled for too long, killing process..."
                    kill $pid 2>/dev/null || true
                    return 1
                fi
            else
                stall_count=0  # Reset stall count if speed is good
            fi
        elif [ $current_size -eq $last_size ]; then
            # No progress in size
            stall_count=$((stall_count + 1))
            echo "⚠️  No progress detected - stall count: ${stall_count}"
            
            if [ $stall_count -ge 6 ]; then  # 3 minutes of no progress
                echo "❌ Download stalled (no progress), killing process..."
                kill $pid 2>/dev/null || true
                return 1
            fi
        fi
        
        last_size=$current_size
        last_check_time=$(date +%s)
    done
    
    # Wait for process to finish and get exit code
    wait $pid
    local exit_code=$?
    echo "Download process exited with code: $exit_code"
    return $exit_code
}

# Main download loop
for attempt in $(seq 1 $MAX_ATTEMPTS); do
    echo "=== Download attempt $attempt/$MAX_ATTEMPTS ==="
    
    # Start the download in background
    echo "Starting ollama pull $MODEL_NAME..."
    ollama pull $MODEL_NAME &
    download_pid=$!
    echo "Download process started with PID: $download_pid"
    
    # Monitor the download
    if monitor_download $download_pid; then
        echo "✅ Model downloaded successfully on attempt $attempt"
        exit 0
    else
        echo "❌ Download failed or stalled on attempt $attempt"
        
        if [ $attempt -lt $MAX_ATTEMPTS ]; then
            echo "Waiting 10 seconds before retry..."
            sleep 10
        fi
    fi
done

echo "❌ Failed to download model after $MAX_ATTEMPTS attempts"
exit 1 