from grabber.Storia import Storia

storia = Storia("https://www.storia.ro/ro/rezultate/vanzare/apartament/bucuresti?limit=36&ownerTypeSingleSelect=ALL&by=BEST_MATCH&direction=DESC&viewType=listing")

storia.fetch_listings()