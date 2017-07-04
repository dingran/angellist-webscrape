import AngelScraper as AS

a = AS.AngelScraper()

a.generate_url_list_of_search_pages(use_existing_url_list=True)
a.parse_all_search_pages()