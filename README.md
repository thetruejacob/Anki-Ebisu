This Anki addon changes the underlying scheduling algorithm; replacing SM2 with Ebisu.

Warning: This change is not reversible and is incompatible with many other addons. This is currently still being tested, so use on a different Anki account.
Addons that change the intervals, such as: Auto Ease Factor, auto lapse new interval, interval booster, avg ease, scheduler: Dynamic Lapse Interval (alpha), scheduler: Reduce Interval growth for very mature cards, update learning steps; are NOT compatible with this addon.



# How it Works
For a full description of the statistical model behind Ebisu, check out [Fasih Ahmed's explanation](https://fasiha.github.io/ebisu/#bernoulli-quizzes).

# How to Install
In your terminal, navigate to the folder where your addons are kept. Then, clone this repo:
```
git clone https://github.com/thetruejacob/Anki-Ebisu
```
Open up Anki and check out your addons. It should be there as Anki-Ebisu

# Acknowledgements 
A huge thanks to Fasih Ahmed for creating Ebisu!

Many thanks also to Arthur Milchior for helping with the addon. The Anki backend is not at all easy to navigate. 
