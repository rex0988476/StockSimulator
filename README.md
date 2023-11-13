# StockSimulator

## Description
Simulate stock market, you can buy and sell stocks.  

## Requirement
* Python
* BeautifulSoup
* selenium
* newest webdriver version

## Usage
0. Download this project and unzip it. (You can download this folder from [here](https://minhaskamal.github.io/DownGit/#/home "DownGit"))  
1. Open `setup.txt`, use the following format to fill in the player link, map mod name and map link.  
```
USER,[player link]
[map mod name 1][x],[map link 1]  
[map mod name 1][x+1],[map link 2]  
[map mod name 2][x],[map link 3]  
...   
```
* `[player link]` is your osu profile link.  
* `[map mod name x]` should be one of `NM`, `HD`, `HR`, `DT`, `FM`, `TB`. The order from top to bottom should be `NM`, `HD`, `HR`, `DT`, `FM`, `TB`. If there is no such mod then leave it blank.
* `[x]` should start from 1 in ascending order.
* `[map link x]` should start at `https://osu.ppy.sh/beatmaps/...`.  
* example:  
![setup](https://github.com/rex0988476/Python/blob/main/Taiko_Tournament_Tools/mp_link_to_score/README/setup.png)  
2. Open `mplink.txt`, paste one multi play link.
* example:  
![mplink](https://github.com/rex0988476/Python/blob/main/Taiko_Tournament_Tools/mp_link_to_score/README/mplink.png)  
3. Make sure you are at the location where `mp_link_to_score.py` is. Then open terminal, use following statement to execute program. It should produce `mp score.txt` as output.
```
python mp_link_to_score.py  
```
4. Open `mp score.txt` and you will see the player's play score in the map from the multi play link.
* example:  
![mp score](https://github.com/rex0988476/Python/blob/main/Taiko_Tournament_Tools/mp_link_to_score/README/mpscore.png)
## Demo
[demo](https://www.youtube.com/watch?v=HeoxKrUldXw "demo")
