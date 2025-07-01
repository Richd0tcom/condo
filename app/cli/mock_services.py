import asyncio
import typer
import uvloop
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

from app.mock.service_orchestrator import service_orchestrator
from app.mock.mock_services import WebhookEventType, WebhookPayloadGenerator, MockServiceTester

app = typer.Typer(name="mock-services", help="Manage mock external services")
console = Console()

@app.command()
def start():
    """Start all mock external services"""
    console.print("🚀 Starting mock external services...", style="bold blue")
    
    async def _start():
        await service_orchestrator.start_services()
        console.print("✅ All mock services are running!", style="bold green")
        console.print("\nService URLs:")
        console.print("  • User Management: http://localhost:8001")
        console.print("  • Payment Service: http://localhost:8002") 
        console.print("  • Communication Service: http://localhost:8003")
        console.print("\nPress Ctrl+C to stop services...")
        
        try:
            # Keep services running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            console.print("\n🛑 Stopping services...", style="bold yellow")
            await service_orchestrator.stop_services()
            console.print("✅ Services stopped", style="bold green")
    
    # Use uvloop for better performance
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    asyncio.run(_start())

@app.command()
def status():
    """Check status of all mock services"""
    console.print("🔍 Checking service status...", style="bold blue")
    
    async def _check_status():
        discovery = service_orchestrator.get_service_discovery()
        health_status = await discovery.health_check_all()
        
        table = Table(title="Mock Services Status")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("URL", style="yellow")
        
        for service_name, is_healthy in health_status.items():
            status = "✅ Healthy" if is_healthy else "❌ Unhealthy"
            url = discovery.get_service_url(service_name)
            table.add_row(service_name, status, url)
        
        console.print(table)
    
    asyncio.run(_check_status())

@app.command()
def test(
    tenant_id: str = typer.Option("test-tenant", help="Tenant ID for testing"),
    service: Optional[str] = typer.Option(None, help="Specific service to test")
):
    """Test mock service integrations"""
    console.print(f"🧪 Testing mock services for tenant: {tenant_id}", style="bold blue")
    
    async def _run_tests():
        discovery = service_orchestrator.get_service_discovery()
        tester = MockServiceTester(discovery)
        
        services_to_test = [service] if service else ["user_management", "payment", "communication"]
        
        with Progress() as progress:
            task = progress.add_task("Running tests...", total=len(services_to_test))
            
            for service_name in services_to_test:
                try:
                    if service_name == "user_management":
                        await tester.test_user_service_integration(tenant_id)
                        console.print(f"✅ {service_name} integration test passed")
                    elif service_name == "payment":
                        await tester.test_payment_service_integration(tenant_id)
                        console.print(f"✅ {service_name} integration test passed")
                    elif service_name == "communication":
                        await tester.test_communication_service_integration(tenant_id)
                        console.print(f"✅ {service_name} integration test passed")
                    else:
                        console.print(f"❌ Unknown service: {service_name}", style="red")
                        
                except Exception as e:
                    console.print(f"❌ {service_name} integration test failed: {e}", style="red")
                
                progress.advance(task)
    
    asyncio.run(_run_tests())

@app.command()
def generate_events(
    tenant_id: str = typer.Option("test-tenant", help="Tenant ID for events"),
    count: int = typer.Option(10, help="Number of events to generate"),
    event_type: Optional[str] = typer.Option(None, help="Specific event type")
):
    """Generate test webhook events"""
    console.print(f"🎯 Generating {count} webhook events for tenant: {tenant_id}", style="bold blue")
    
    async def _generate_events():
        registry = service_orchestrator.get_service_registry()
        generator = WebhookPayloadGenerator()
        
        event_types = {
            "user_created": ("user_management", "USER_CREATED"),
            "user_updated": ("user_management", "USER_UPDATED"),
            "payment_succeeded": ("payment", "PAYMENT_SUCCEEDED"),
            "payment_failed": ("payment", "PAYMENT_FAILED"),
            "email_delivered": ("communication", "EMAIL_DELIVERED"),
            "email_failed": ("communication", "EMAIL_FAILED")
        }
        
        if event_type and event_type not in event_types:
            console.print(f"❌ Unknown event type: {event_type}", style="red")
            return
        
        events_to_generate = [event_type] if event_type else list(event_types.keys())
        
        for i in range(count):
            for event_name in events_to_generate:
                service_name, webhook_event_type = event_types[event_name]
                
                # Generate appropriate event
                if "user" in event_name:
                    event = generator.generate_user_event(tenant_id, getattr(WebhookEventType, webhook_event_type))
                elif "payment" in event_name:
                    event = generator.generate_payment_event(tenant_id, getattr(WebhookEventType, webhook_event_type))
                elif "email" in event_name:
                    event = generator.generate_notification_event(tenant_id, getattr(WebhookEventType, webhook_event_type))
                
                # Send webhook
                await registry.send_webhook(service_name, event)
                console.print(f"📤 Generated {event_name} event: {event.id}")
    
    asyncio.run(_generate_events())

if __name__ == "__main__":
    app()
