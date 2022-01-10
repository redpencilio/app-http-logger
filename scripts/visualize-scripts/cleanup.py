#!/usr/bin/env python3
import argparse
import datetime
import requests
import logging

class Arguments:
    def parse(self):
        parser = argparse.ArgumentParser("cleanup")

        before_date_parser = parser.add_mutually_exclusive_group(required=True)
        before_date_parser.add_argument('--before-date', type=self.parse_before_date, help='Log entries from before this date (YYYY-MM-DD) will be deleted.')
        before_date_parser.add_argument('--older-than-days', type=self.parse_older_than_days, dest='before_date', help='Log entries older than this number of days will be deleted.')
        parser.add_argument('--index-pattern',  default="http-log*,stats*", type=str, help="Comma-separated list of index patterns to clear. Default: \"http-log*,stats*\". Use * for wildcard.")
        parser.add_argument('--elasticsearch-url', default="http://elasticsearch:9200")

        args = parser.parse_args()

        return args

    def parse_before_date(self, s):
        date = datetime.datetime.strptime(s, '%Y-%m-%d').date()
        self.ensure_past(date)
        return date

    def parse_older_than_days(self, s):
        date = datetime.date.today() - datetime.timedelta(days=int(s))
        self.ensure_past(date)
        return date

    def ensure_past(self, date):
        if date > datetime.date.today():
            raise argparse.ArgumentError()


def es_cleanup(elasticsearch_url: str, index_pattern: str, before_date: datetime.date):
    request_headers = { 'content-type' : 'application/json' }
    request_body = {
        "query": {
            "range": {
                "@timestamp": {
                    "lt": before_date.isoformat()
                }
            }
        }
    }
    # https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-delete-by-query.html
    response = requests.post(f"{elasticsearch_url}/{index_pattern}/_delete_by_query", headers=request_headers, json=request_body)
    response.raise_for_status()
    response_body = response.json()
    return response_body["deleted"]


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)

    arguments = Arguments()
    args = arguments.parse()

    answer = input(f'All log entries from indexes matching "{args.index_pattern}" dating from before {args.before_date} will be deleted. Are you sure? [y/N]')
    if answer.lower() != "y":
        exit()

    deleted_count = es_cleanup(args.elasticsearch_url, args.index_pattern, args.before_date)

    logging.info(f"I deleted {deleted_count} log entries.")

    # TODO: It is probably useful to delete empty indices when using the *-visualize-pipelines.
    # These pipelines create an index for each day.
    # They become obsolete when the log data has been cleared for that day.
