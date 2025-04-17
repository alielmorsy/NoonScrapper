from typing import Dict, List, Union

from lxml import html
import csv


def _get_item_counter(html_content) -> int:
    """
    A simple utility function that determine how many pages that search query have.
    :param html_content: the HTML text to be parsed
    :return: an integer count of how many pages that search query have been found
    """
    tree = html.fromstring(html_content)
    page_items = tree.xpath('//ul[@role="navigation"]//li')
    page_numbers = []

    for li in page_items:
        li_content = li.text_content().strip()
        if li_content.isdigit():
            page_numbers.append(int(li_content))

    # Get the highest number (last page)
    total_pages = max(page_numbers) if page_numbers else 1
    return total_pages


def clean_number(number: str) -> float:
    return float(number.strip().replace(",", ""))


def extract_products(html_content: str) -> List[Dict[str, Union[str, float]]]:
    """
    Extract the products from the HTML content.
    :param html_content: Text represents the products page
    :return: A list of dictionaries, each dictionary represents a product and contains relative path,selling price, old price, and rating.
    """
    tree = html.fromstring(html_content)
    product_items = tree.xpath('//a[contains(@class, "ProductBoxLinkHandler_productBoxLink")]')
    products = []

    for item in product_items:
        product = {"path": item.attrib['href']}

        selling_price = item.xpath('.//strong[contains(@class, "Price_amount")]/text()')
        rating = item.xpath('.//div[contains(@class, "RatingPreviewStar_textCtr")]/text()')
        old_price_list = item.xpath('.//span[contains(@class, "Price_oldPrice")]/text()')

        if selling_price:
            product["selling_price"] = clean_number(selling_price[0])
        else:
            product["selling_price"] = float("nan")

        if rating:
            product["rating"] = clean_number(rating[0])
        else:
            product["rating"] = float("nan")

        if old_price_list:
            product["old_price"] = clean_number(old_price_list[0])
        else:
            product["old_price"] = float("nan")

        products.append(product)

    return products


def write_to_disk(file_name: str, products: List[Dict[str, Union[str, float]]]) -> None:
    """
       Writes a list of dictionaries to a CSV file on disk.
       :param file_name: The path to the output CSV file.
       :param products: The list of dictionaries to write.
       """
    if not products:
        raise ValueError("The input data list is empty.")

    # Extract fieldnames (keys of the first dictionary)
    fieldnames = products[0].keys()

    # Write to CSV
    with open(file_name, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header
        writer.writeheader()

        # Write rows
        writer.writerows(products)
