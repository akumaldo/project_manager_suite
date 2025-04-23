 #!/bin/bash
set -e

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Setting up Product Discovery Hub...${NC}"

# Create Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install backend dependencies
echo -e "${YELLOW}Installing backend dependencies...${NC}"
pip install -r requirements.txt

# Check if .env file exists, create a template if it doesn't
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env template file...${NC}"
    cat > .env << EOF
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
SUPABASE_JWT_SECRET=your_supabase_jwt_secret
OPENROUTER_API_KEY=your_openrouter_api_key
HOST=localhost
PORT=8000
ENVIRONMENT=development
EOF
    echo -e "${YELLOW}⚠️  Please update the .env file with your actual values before continuing.${NC}"
    echo -e "${YELLOW}Press Enter to continue or Ctrl+C to abort and update the .env file...${NC}"
    read
fi

# Check if frontend directory exists
if [ -d "frontend" ]; then
    # Frontend is in a subdirectory called "frontend"
    FRONTEND_DIR="frontend"
elif [ -d "client" ]; then
    # Frontend is in a subdirectory called "client"
    FRONTEND_DIR="client"
elif [ -f "package.json" ]; then
    # Frontend is in the same directory as backend
    FRONTEND_DIR="."
else
    # No frontend detected
    FRONTEND_DIR=""
    echo -e "${YELLOW}⚠️  No frontend directory detected. Will only start the backend.${NC}"
fi

# Start backend and frontend in separate terminals
if [ -n "$FRONTEND_DIR" ]; then
    # If frontend exists, start both
    echo -e "${GREEN}Starting backend and frontend servers...${NC}"
    
    # Check which terminal command to use
    if command -v osascript &> /dev/null && [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - use AppleScript to open new Terminal windows
        osascript -e "tell application \"Terminal\" to do script \"cd $(pwd) && source venv/bin/activate && python run.py\""
        
        # Check what package manager to use for frontend
        if [ -f "$FRONTEND_DIR/yarn.lock" ]; then
            osascript -e "tell application \"Terminal\" to do script \"cd $(pwd)/$FRONTEND_DIR && yarn && yarn dev\""
        else
            osascript -e "tell application \"Terminal\" to do script \"cd $(pwd)/$FRONTEND_DIR && npm install && npm run dev\""
        fi
    elif command -v gnome-terminal &> /dev/null; then
        # Linux with GNOME - use gnome-terminal
        gnome-terminal -- bash -c "cd $(pwd) && source venv/bin/activate && python run.py; exec bash"
        
        if [ -f "$FRONTEND_DIR/yarn.lock" ]; then
            gnome-terminal -- bash -c "cd $(pwd)/$FRONTEND_DIR && yarn && yarn dev; exec bash"
        else
            gnome-terminal -- bash -c "cd $(pwd)/$FRONTEND_DIR && npm install && npm run dev; exec bash"
        fi
    elif command -v x-terminal-emulator &> /dev/null; then
        # Generic Linux
        x-terminal-emulator -e "bash -c 'cd $(pwd) && source venv/bin/activate && python run.py; exec bash'"
        
        if [ -f "$FRONTEND_DIR/yarn.lock" ]; then
            x-terminal-emulator -e "bash -c 'cd $(pwd)/$FRONTEND_DIR && yarn && yarn dev; exec bash'"
        else
            x-terminal-emulator -e "bash -c 'cd $(pwd)/$FRONTEND_DIR && npm install && npm run dev; exec bash'"
        fi
    else
        # Fallback - run backend in background and frontend in foreground
        echo -e "${YELLOW}Unable to open multiple terminal windows automatically.${NC}"
        echo -e "${YELLOW}Starting backend in the background and frontend in the foreground...${NC}"
        
        (cd $(pwd) && source venv/bin/activate && python run.py) &
        BACKEND_PID=$!
        
        echo -e "${GREEN}Backend started with PID $BACKEND_PID${NC}"
        echo -e "${GREEN}Starting frontend...${NC}"
        
        cd $FRONTEND_DIR
        if [ -f "yarn.lock" ]; then
            yarn && yarn dev
        else
            npm install && npm run dev
        fi
        
        # When frontend is terminated, kill the backend too
        kill $BACKEND_PID
    fi
else
    # No frontend detected, just start the backend
    echo -e "${GREEN}Starting backend server...${NC}"
    python run.py
fi