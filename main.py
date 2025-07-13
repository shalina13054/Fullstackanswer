import argparse
from pubmed_fetcher.fetcher import fetch_pubmed_ids, fetch_pubmed_details, save_to_csv


def main():
    parser = argparse.ArgumentParser(description="Fetch PubMed papers based on query.")
    parser.add_argument("query", type=str, help="Search query for PubMed.")
    parser.add_argument("-f", "--file", type=str, default="", help="Output CSV file name.")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output.")

    args = parser.parse_args()
    if args.debug:
        print(f"Query: {args.query}")

    ids = fetch_pubmed_ids(args.query)
    if args.debug:
        print(f"Fetched IDs: {ids}")

    results = fetch_pubmed_details(ids)

    if args.file:
        save_to_csv(results, args.file)
    else:
        for r in results:
            print(r)


if __name__ == "__main__":
    main()
