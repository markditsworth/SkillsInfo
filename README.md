# SkillsInfo
### An environment for geospatailly analyzing skills in the labor market

SkillsInfo makes available a Selenium webscraper for LinkedIn crawling, Google's [Geocoding API](https://developers.google.com/maps/documentation/geocoding/start) for enriching information acquired by the webcrawler, and the ELK stack for storage, rapid full-text searching, and geospatial viziualization.

### Example

### Architecture Diagram

### Dependencies
- A Linux host machine
- Python3
- Docker
- A Google Geocoding API Key
- A LinkedIn account

### How To Run:
1. Ensure all dependencies are satisfied and clone the repo
2. Run `./build_environment.sh` to create the python venv and to pull the needed docker images
3. Edit the `logstash/pipeline.yml` file to make logstash read from the topic you will search for. E.g. if you pass in `--topic computer_vision` to the scraper, the topic to read from should be `parsed-computer_vision`.
4. Run `./launch_stack.sh` to spin up your infrastructure.
5. Run the following to start crawling LinkedIn for your desired skills
```bash
cd python
source LI-Scraper/bin/activate
python scraper.py --topic <skill_to_search_spaces_as_underscores> --username <your linkedin username> --password <your linkedin pasword> [ --backup (to write to local json file) --limit n (n number of google pages to consider)] 
```
6. Run the following in a separate terminal window to start parsing
```bash
cd python
source LI-Scraper/bin/activate
python parseGeo.py --topic <same topic you passed in to the scraper> [ --from-file (if you're reading from file. Omit if you consume from kafka) ]
```
7. Data should start showing up in Kibana. Navigate to `localhost:5601` in your browser. Create your index pattern(s), and navigate to Visualizations to create the map visualization.

### Note
Running Kafka, the ELK stack, and Chrome all at once is very memory intensive. If need be, make use of the `--backup` and `--from-file` functionality to store LinkedIn info to disk, and only spin up ELK once the web scraping has finished.
