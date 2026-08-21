# YouTube-Top-History
Scoreboard of your most watched youtube videos per years or months

## Known Bugs
- For linux users, some more extra fonts have not been manually added to
Matplolib (they're compatible but too extra for matplot to auto-register them)
- I'm not doing sanity check on year/month input, if they are no compatible entries in your input file
- Google Takeout sometimes replace author name with the url (sight), I'm not handling this yet (fixing this ASAP because it's messing up the counter)
I'm working on it whenever I have the time !

## Credits
I came accross biast12 works on the subject  
https://gist.github.com/biast12/dafc5d6e33612953e3e4da2ea54cd305

Unfortunately, this does not work on my side (even though it's only 4 months old)
I guess Google made changes in the meantime.  
Anyways ! Maybe you should try biast12 script first and see how it goes !


I decided to do my own script since I wanted very specific things
- Generating pictures with a scoreboard of most watched => per months and per year
- Crawling Youtube history (not only Youtube Music since I rarely use it)
- Clickable links inside the output pictures
- HTML viewer (easier to interact with clickable links)

Also using this for journaling purposes so I'm using this each new month haha

If your goal is to have scoreboard from your full youtube history, you should
check biast12 script (you can quickly adapt it to search for Youtube as a whole)

## Manual Requirement
No simple other way around
### Export your data from Google Takeout
- Get your data export from https://takeout.google.com/
- Deselect all, scroll till the end of the page and only select "Youtube and Youtube Music"
There are 2 sections under "Youtube and Youtube Music"
- Multiples formats : Select either format (HTML file is heavier)
- All Youtube data included : Only select "history"

## Usage
### Install Env & Requirements
```bash
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

### Run
```bash
./youtube-top-history.py --file-path "path/somewhere/wath-history.html" --top 50
```
- `-h/--help`: Print usage
- `--file-path [STRING]`: Path to your watch\_history file
- `--top [INTEGER]`: Number of top videos for the scoreboard, recommend 10, 50, 100 (default is 10)
- `--today`: Get the scoreboard of this month
- `--month [01-12] or --month [STRING]`: Get the scoreboard of specified month
- `--year [INTEGER]`: Get the scoreboard of the specified year
- `--all-month`: Get the scoreboard for each months of the current(default) or specified year
- `--all-year`: Get the scoreboard for each years
- `--all`: Get the scoreboard for each years + each months of every years
- `--export-html`: Generate a html view of your svg figures

### Examples
Get the scoreboard of the current month
```bash
./youtube-top-history.py --file-path watch-history.html --today
```

## TODO
- [X] Clickable links inside the output pictures
- [X] Read JSON format ?
- [ ] --history option to get the scoreboard from your full history on youtube
- [X] Pretty progress bar
- [ ] Try to get input data from Youtube API ?
- [ ] GUI
- [ ] Build MacOS font compatibility

## Authors
Amandine N. "AnSpake" <AnSpake@proton.me>  
https://github.com/AnSpake/Youtube-Top-History
