# memorize-anki
Implementation of MEMORIZE in an Anki addon.

Ideally, you should be cloning directy into the add-on folder. 
For me, it's at /Users/jacob/Library/Application Support/Anki2/addons21

and then test it from the anki side. 

The following repos were heavily used to inform this one.

# Resources
Repos
- https://github.com/eshapard/experimentalCardEaseFactor/
- https://github.com/duolingo/halflife-regression
- https://github.com/Networks-Learning/memorize
- https://github.com/dae/anki
- https://github.com/lovac42/ReMemorize



Anki
- https://github.com/ankidroid/Anki-Android/wiki/Database-Structure
- The debug console is cmd ;


MEMORIZE Resources
- https://www.reddit.com/r/Anki/comments/cghyiy/optimized_spaced_repetition_algorithm/ (Utkarsh reponds)
- http://learning.mpi-sws.org/memorize/

Making an Addon
- https://www.juliensobczak.com/write/2016/12/26/anki-scripting.html

Paying
- https://www.reddit.com/r/Anki/comments/e0dazp/how_does_the_anki_community_feel_about_paying_for/



# Goals: 
1. Find how Shepard did his experimentalcardeasefactor
2. Try to implement a small-scale prediction model that can scrape data from the history
3. Try to implement Tabibian's model, and make it update all of the cards. 

Add a button that updates all the cards following Tabibian's model. 

# REPL Testing
- Make changes, restart Anki

