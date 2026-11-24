# Draft: permission request to Etherscan

Draft only. The user fills in the placeholders and sends it through Etherscan's contact form or support address.

---

**Subject:** Permission request: Etherscan-derived labels in non-commercial academic research

Dear Etherscan team,

My name is [Your name], and I am a researcher at [affiliation]. I am building a machine-learning model of Ethereum activity to detect scam tokens, such as rug pulls and honeypots, soon after they launch. The work is non-commercial academic research and will be submitted for publication.

Your Terms of Service (section 8) and API terms restrict using Etherscan data, including data obtained through third parties, for machine learning. Before using any such data, I would like to ask for your permission for two uses:

1. **Phishing labels from the B4E dataset.** B4E was released with the BERT4ETH paper (Hu et al., WWW 2023). Its labels come from the Etherscan "Phish/Hack" tag: about 3,220 phishing accounts and 594,038 normal accounts, with their transactions up to May 2022. I would use these labels to train and evaluate a phishing classifier, so our results can be compared with BERT4ETH's published results.
2. **Address labels for exchange wallets.** One test checks whether the model can recognise centralised-exchange wallets. I am building that exchange list from the exchanges' own proof-of-reserves disclosures. I would like to use Etherscan's exchange name tags only to check that list for missing or wrong addresses, not as training labels.

What I would and would not do:

- Use the data only for this research project.
- Not resell, redistribute or republish the labels or any Etherscan data, and not build a commercial product or service from them.
- Publish only aggregate results, such as accuracy and precision figures, with credit to Etherscan as the source of the labels. No Etherscan-derived label for any address would be published.
- Not scrape Etherscan or use the Etherscan API to collect more data.

If you can grant permission, or would prefer different conditions, I would be glad to follow them. If not, I will leave these labels out of the study.

Thank you for your time.

Kind regards,
[Your name]
[affiliation]
