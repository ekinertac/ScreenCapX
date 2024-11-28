# Variables
PYTHON := python  # Replace with your Python interpreter if needed (e.g., python3.9)
APP_SCRIPT := ScreenCapX.py
SETUP_SCRIPT := setup.py

.PHONY: all build clean run test

# Default target
all: clean build

# Run the development build
dev:
	$(PYTHON) $(APP_SCRIPT) py2app -A
	./dist/ScreenCapX.app/Contents/MacOS/ScreenCapX

# Build the macOS app using py2app
build:
	@echo "Building the macOS app..."
	$(PYTHON) $(SETUP_SCRIPT) py2app --no-strip

# Clean up the dist and build directories
clean:
	@echo "Cleaning up..."
	rm -rf dist build
	@echo "Cleaned up dist and build folders."

# Run the app directly with Python
run:
	@echo "Running the script directly..."
	$(PYTHON) $(APP_SCRIPT)

# Test bundling without creating the final app
test:
	@echo "Testing setup.py (dry-run)..."
	$(PYTHON) $(SETUP_SCRIPT) py2app --dry-run

# Rebuild: Clean and then build
rebuild: clean build
	@echo "Rebuild completed."

# Help message
help:
	@echo "Makefile for managing py2app operations:"
	@echo "  make          - Default target (clean + build)"
	@echo "  make build    - Build the app using py2app"
	@echo "  make clean    - Remove dist and build folders"
	@echo "  make run      - Run the script directly with Python"
	@echo "  make test     - Test the setup.py script (dry-run)"
	@echo "  make rebuild  - Clean and rebuild the app"
	@echo "  make help     - Show this help message"
