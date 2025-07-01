import asyncio
import signal
import sys
from pathlib import Path
import uvloop
from rich.console import Console
from rich.panel import Panel

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.mock.service_orchestrator import service_orchestrator

console = Console()

class MockServiceRunner:
    def __init__(self):
        self.running = True
        
    async def start(self):
        """Start all mock services"""
        console.print(Panel.fit(
            "🚀 Starting Mock External Services",
            style="bold blue"
        ))
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Start services
            await service_orchestrator.start_services()
            
            console.print("\n✅ All services started successfully!", style="bold green")
            console.print("\n📋 Service Endpoints:")
            console.print("  • User Management: http://localhost:8001")
            console.print("  • Payment Service: http://localhost:8002")
            console.print("  • Communication Service: http://localhost:8003")
            console.print("\n🔍 Health Checks:")
            console.print("  • http://localhost:8001/health")
            console.print("  • http://localhost:8002/health") 
            console.print("  • http://localhost:8003/health")
            console.print("\n📖 API Documentation:")
            console.print("  • http://localhost:8001/docs")
            console.print("  • http://localhost:8002/docs")
            console.print("  • http://localhost:8003/docs")
            
            console.print("\n⚡ Press Ctrl+C to stop services...\n", style="yellow")
            
            # Keep running until signal
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            pass
        finally:
            await self._cleanup()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        console.print("\n🛑 Received shutdown signal...", style="yellow")
        self.running = False
    
    async def _cleanup(self):
        """Cleanup resources"""
        console.print("🧹 Cleaning up services...", style="yellow")
        await service_orchestrator.stop_services()
        console.print("✅ Services stopped cleanly", style="green")

async def main():
    # Use uvloop for better performance
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    
    runner = MockServiceRunner()
    await runner.start()

if __name__ == "__main__":
    asyncio.run(main())