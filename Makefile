run-dashboard:
	streamlit run dashboard.py

gen-sample:
	python generator.py --topic "Paid Ads in B2B" --audience "B2B founders and performance marketers" --primary_keyword "B2B paid ads" --author_name "WIF Marketing" --author_title "Performance Marketing Agency" --year 2025 --use_ai false
