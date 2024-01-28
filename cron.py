import asyncio
import sys

from app.cron.newsJob import run_news_cron_job, run_getNews_for_one_corporation


async def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py [language|location|news]")
        sys.exit(1)

    job_type = sys.argv[1]

    if job_type == 'news':
        print("LOG: Running news job...")
        await run_news_cron_job()
    elif job_type == 'getNews':
        print("LOG: getting news job for specific organization...")
        if len(sys.argv) < 2:
            print("Usage: python script.py getNews [organizationName]")
            sys.exit(1)

        organization_name = sys.argv[2]
        await run_getNews_for_one_corporation(organization_name)


if __name__ == "__main__":
    asyncio.run(main())
