"""CostPilot CLI — Cloud Cost Optimization Engine."""

import click
import logging
from .analyzer import CostAnalyzer
from .rightsizer import RightSizer
from .unused import UnusedDetector
from .reporter import ReportGenerator
from .config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


@click.group()
@click.option("--profile", default=None, help="AWS profile name")
@click.option("--region", default="us-east-1", help="AWS region")
@click.pass_context
def cli(ctx: click.Context, profile: str, region: str) -> None:
    """☁️ CostPilot — AWS Cloud Cost Optimization Engine."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = Config(profile=profile, region=region)


@cli.command()
@click.option("--days", default=30, help="Analysis period in days (30/60/90)")
@click.option("--output", default="report", help="Output directory")
@click.pass_context
def analyze(ctx: click.Context, days: int, output: str) -> None:
    """Run full cost analysis with recommendations."""
    config = ctx.obj["config"]
    click.echo(f"🔍 Analyzing {days} days of AWS cost data...")

    analyzer = CostAnalyzer(config)
    results = analyzer.analyze(days=days)

    rightsizer = RightSizer(config)
    sizing = rightsizer.analyze()

    detector = UnusedDetector(config)
    unused = detector.scan()

    reporter = ReportGenerator(config)
    reporter.generate(results, sizing, unused, output_dir=output)

    total_savings = results.get("potential_savings", 0) + sizing.get("potential_savings", 0) + unused.get("potential_savings", 0)
    click.echo(f"\n💰 Total potential savings: ${total_savings:,.2f}/month")
    click.echo(f"📄 Report saved to {output}/")


@cli.command()
@click.option("--output", default="report", help="Output directory")
@click.pass_context
def report(ctx: click.Context, output: str) -> None:
    """Generate cost report from latest analysis."""
    config = ctx.obj["config"]
    reporter = ReportGenerator(config)
    click.echo(f"📊 Generating report...")
    reporter.generate_from_cache(output_dir=output)
    click.echo(f"📄 Report saved to {output}/")


@cli.command()
@click.pass_context
def unused(ctx: click.Context) -> None:
    """Find unused/idle AWS resources."""
    config = ctx.obj["config"]
    detector = UnusedDetector(config)
    click.echo("🔎 Scanning for unused resources...")

    results = detector.scan()
    total = results.get("total_unused", 0)
    savings = results.get("potential_savings", 0)

    click.echo(f"\n📋 Found {total} unused resources")
    click.echo(f"💰 Potential savings: ${savings:,.2f}/month")

    for category, items in results.get("resources", {}).items():
        if items:
            click.echo(f"\n  {category}:")
            for item in items[:5]:
                click.echo(f"    • {item['id']} — ${item.get('monthly_cost', 0):.2f}/mo")


@cli.command()
@click.option("--budget", required=True, type=float, help="Monthly budget in USD")
@click.option("--email", required=True, help="Alert email address")
@click.pass_context
def watch(ctx: click.Context, budget: float, email: str) -> None:
    """Set up budget alerts."""
    config = ctx.obj["config"]
    from .alerts import AlertManager
    manager = AlertManager(config)
    click.echo(f"⏰ Setting up ${budget:,.0f}/month budget alert...")
    manager.create_budget_alert(budget=budget, email=email)
    click.echo(f"✅ Budget alert created. Notifications at 50%, 75%, 90%, 100%.")


def main() -> None:
    cli(obj={})


if __name__ == "__main__":
    main()
