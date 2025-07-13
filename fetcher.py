import requests
import xmltodict
import csv
from typing import List, Dict
from tqdm import tqdm


def is_pharma_affiliation(affiliation: str) -> bool:
    pharma_keywords = ["pharma", "biotech", "therapeutics", "inc", "llc"]
    return any(keyword in affiliation.lower() for keyword in pharma_keywords)


def is_non_academic_affiliation(affiliation: str) -> bool:
    academic_keywords = ["university", "college", "institute", "school"]
    return not any(keyword in affiliation.lower() for keyword in academic_keywords)


def fetch_pubmed_ids(query: str) -> List[str]:
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db": "pubmed", "term": query, "retmode": "json", "retmax": 100}
    response = requests.get(url, params=params)
    return response.json()["esearchresult"]["idlist"]


def fetch_pubmed_details(paper_ids: List[str]) -> List[Dict]:
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(paper_ids),
        "retmode": "xml"
    }
    response = requests.get(url, params=params)
    articles = xmltodict.parse(response.content)["PubmedArticleSet"]["PubmedArticle"]

    results = []

    for article in tqdm(articles if isinstance(articles, list) else [articles]):
        try:
            medline = article["MedlineCitation"]
            article_data = medline["Article"]
            authors = article_data.get("AuthorList", {}).get("Author", [])
            if not isinstance(authors, list):
                authors = [authors]

            pharma_authors = []
            non_academic_authors = []
            email = ""
            company_affiliations = []

            for author in authors:
                aff_info = author.get("AffiliationInfo")
                if aff_info:
                    aff_text = aff_info[0]["Affiliation"]
                    if is_pharma_affiliation(aff_text):
                        company_affiliations.append(aff_text)
                    if is_non_academic_affiliation(aff_text):
                        non_academic_authors.append(
                            f"{author.get('ForeName', '')} {author.get('LastName', '')}".strip()
                        )
                    if "@" in aff_text:
                        email = aff_text.split()[-1]  # crude email grab

            if company_affiliations:
                results.append({
                    "PubmedID": medline["PMID"]["#text"],
                    "Title": article_data["ArticleTitle"],
                    "Publication Date": article_data["Journal"]["JournalIssue"]["PubDate"].get("Year", "Unknown"),
                    "Non-academic Author(s)": "; ".join(non_academic_authors),
                    "Company Affiliation(s)": "; ".join(company_affiliations),
                    "Corresponding Author Email": email
                })
        except Exception as e:
            print(f"Error parsing article: {e}")

    return results


def save_to_csv(data: List[Dict], filename: str):
    if not data:
        print("No data to write.")
        return
    keys = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        dict_writer = csv.DictWriter(f, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
