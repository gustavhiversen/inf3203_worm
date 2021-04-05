# Spawn N segments on host C(host:port) 
    ./wormgate_http.sh -o bin -c C -n N

# Kill all segments on all gates
    ./wormgate_http.sh -o kill_all

# Get Info from gate C
    ./wormgate_http.sh -o info -c C

# Kill all segments on gate C
    ./wormgate_http.sh -o kill -c C



# Get info from segment C
    ./segment_http.sh -o info -c C

# Kill segment C
    ./segment_http.sh -o kill -c C

# Set max segments (can only be sent to leader) to size N
    ./segment_http.sh -o set_max_size -c C