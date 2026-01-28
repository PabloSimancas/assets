Write-Host "Rebuilding and updating containers..."
docker-compose up -d --build
Write-Host "Update complete! Frontend is running at http://localhost:3002"
