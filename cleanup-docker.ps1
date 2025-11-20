# cleanup-docker.ps1
# Script để dọn dẹp Docker (images, cache, volumes, containers)
# Usage: .\cleanup-docker.ps1 [--dry-run] [--aggressive]

param(
    [switch]$DryRun = $false,
    [switch]$Aggressive = $false
)

Write-Host "🧹 Docker Cleanup Script" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "⚠️  DRY RUN MODE - No changes will be made" -ForegroundColor Yellow
    Write-Host ""
}

# Function to run docker command with error handling
function Invoke-DockerCommand {
    param(
        [string]$Command,
        [string]$Description
    )
    
    Write-Host "📋 $Description..." -ForegroundColor Green
    
    if ($DryRun) {
        Write-Host "   [DRY RUN] Would run: $Command" -ForegroundColor Gray
        return
    }
    
    try {
        $output = Invoke-Expression $Command 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✓ Success" -ForegroundColor Green
            if ($output) {
                Write-Host $output -ForegroundColor Gray
            }
        } else {
            Write-Host "   ⚠️  Warning: Command completed with exit code $LASTEXITCODE" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ❌ Error: $_" -ForegroundColor Red
    }
    Write-Host ""
}

# Step 1: Stop containers
Invoke-DockerCommand -Command "docker-compose down -v" -Description "Stopping containers and removing volumes"

# Step 2: Remove stopped containers
Invoke-DockerCommand -Command "docker container prune -f" -Description "Removing stopped containers"

# Step 3: Remove unused images
if ($Aggressive) {
    Invoke-DockerCommand -Command "docker image prune -a -f" -Description "Removing ALL unused images (aggressive)"
} else {
    Invoke-DockerCommand -Command "docker image prune -f" -Description "Removing dangling images"
}

# Step 4: Remove build cache
Invoke-DockerCommand -Command "docker builder prune -f" -Description "Removing build cache"

if ($Aggressive) {
    Invoke-DockerCommand -Command "docker builder prune -a -f" -Description "Removing ALL build cache (aggressive)"
}

# Step 5: Remove unused volumes
Invoke-DockerCommand -Command "docker volume prune -f" -Description "Removing unused volumes"

# Step 6: Remove unused networks
Invoke-DockerCommand -Command "docker network prune -f" -Description "Removing unused networks"

# Step 7: System prune
if ($Aggressive) {
    Invoke-DockerCommand -Command "docker system prune -a -f --volumes" -Description "Full system prune (aggressive)"
} else {
    Invoke-DockerCommand -Command "docker system prune -f" -Description "System prune"
}

# Step 8: Show disk usage
Write-Host "📊 Docker Disk Usage:" -ForegroundColor Cyan
if (-not $DryRun) {
    try {
        docker system df
    } catch {
        Write-Host "   Could not get disk usage info" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "✅ Cleanup completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Usage tips:" -ForegroundColor Cyan
Write-Host "  .\cleanup-docker.ps1           - Normal cleanup" -ForegroundColor Gray
Write-Host "  .\cleanup-docker.ps1 --dry-run - Preview what would be cleaned" -ForegroundColor Gray
Write-Host "  .\cleanup-docker.ps1 --aggressive - Remove ALL unused resources" -ForegroundColor Gray

