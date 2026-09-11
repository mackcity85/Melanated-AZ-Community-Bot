# ==========================================================
# Melanated AZ Real Games
# dirty_minds.py
#
# Multiplayer Dirty Minds game engine.
#
# Features:
#   - Multiplayer rooms
#   - 149 Dirty Minds clues
#   - 10 random rounds per game
#   - Synchronized rounds
#   - Server-side answer validation
#   - Score tracking
#   - Host controls
#   - Reveal answers
#   - Next-round controls
#   - Safe public game state
#
# IMPORTANT:
# Answers are NEVER exposed to the browser until reveal.
# ==========================================================

from __future__ import annotations

import random
import re
import time
from typing import Any


# ==========================================================
# GAME SETTINGS
# ==========================================================

TOTAL_ROUNDS = 10
POINTS_PER_CORRECT_ANSWER = 1


# ==========================================================
# DIRTY MINDS CLUE BANK
#
# 149 clues from your supplied Dirty Minds list.
#
# The clues are intentionally suggestive/misleading while
# the actual answers are ordinary, clean objects or actions.
# ==========================================================

DIRTY_MINDS_CLUES: list[dict[str, Any]] = [

    {
        "clue": 'What starts with a C and ends with a T, is hairy, oval, Delicious, and contains thin whitish liquid?',
        "answer": 'Coconut',
        "aliases": [],
    },
    {
        "clue": 'What goes in hard and pink then comes out soft and sticky?',
        "answer": 'Bubble gum',
        "aliases": [],
    },
    {
        "clue": 'A finger goes in me. You fiddle with me when you’re bored. The best man always has me first.',
        "answer": 'A wedding ring',
        "aliases": ['wedding ring'],
    },
    {
        "clue": 'I come in many sizes. Sometimes, I drip. When you blow me, you feel good.',
        "answer": 'Nose',
        "aliases": [],
    },
    {
        "clue": 'What word starts with an ‘F’ and ends in ‘K’ & if you don’t get it, you have to use your hand.',
        "answer": 'Fork',
        "aliases": [],
    },
    {
        "clue": 'What part of the man has no bone but has muscles, has lots of veins, like pumping, & is responsible for making love?',
        "answer": 'Heart',
        "aliases": [],
    },
    {
        "clue": 'I have fuzzy balls Someone’s going to be beaten. You start off with love, but that doesn’t last…',
        "answer": 'Tennis',
        "aliases": [],
    },
    {
        "clue": 'I’m long, hard, and powered by batteries, I give off a steady stream, and people grope for me in the dark.',
        "answer": 'Torch',
        "aliases": [],
    },
    {
        "clue": 'Playing with me long enough could make you go blind – you have to stick something in my slot before you get started – playing with my joystick can give you a cramp. What am I?',
        "answer": 'Video game',
        "aliases": [],
    },
    {
        "clue": 'Press the right button and I’ll come all over your face – I usually get spread over your hairy parts – when you wipe me off, I get white stuff on your towel. What am I?',
        "answer": 'Shaving cream',
        "aliases": [],
    },
    {
        "clue": 'Can be hard or soft and still get it off – finger my plunger and I’ll come in your hand – I always come in hotel bathrooms. What am I?',
        "answer": 'Soap dispenser',
        "aliases": [],
    },
    {
        "clue": 'You suck on me with your mouth – I can’t stay hard forever – there’s sometimes lipstick on my stick when you’re done. What am I?',
        "answer": 'Icepole',
        "aliases": [],
    },
    {
        "clue": 'The situation was alarming. several large men had to go down on me. At least most of them were wearing rubbers and raincoats before they wrapped their legs around me. – What am I?',
        "answer": 'Firepole',
        "aliases": [],
    },
    {
        "clue": 'I start with “C” – I end with “T” – I stand for pussy, what am I?',
        "answer": 'Cat',
        "aliases": [],
    },
    {
        "clue": 'My shaft is long and tasty – you can shove me in your split – the older I am, the softer I get, what am I?',
        "answer": 'A banana',
        "aliases": ['banana'],
    },
    {
        "clue": 'They are all fakes and Dolly Parton has some big ones. it can cost you a lot of money for a good one, but at least you can pick the size and color.',
        "answer": 'A wig',
        "aliases": ['wig'],
    },
    {
        "clue": 'There it was. Six inches of pure delight beckoned me to take it in my mouth. I ran my tongue around it and its sweet nuts, but the longer I sucked on it, the smaller it got!. What am I?',
        "answer": 'A chocolate bar',
        "aliases": ['chocolate bar'],
    },
    {
        "clue": 'When I go down on you, you won’t be happy. If you’re on me, the whole world is your oyster, but be careful, without protection, you might catch something nasty. What am I?',
        "answer": 'Internet',
        "aliases": [],
    },
    {
        "clue": 'What’s a thing that you can find in a man’s pants but not in a woman’s?',
        "answer": 'Pockets',
        "aliases": [],
    },
    {
        "clue": 'Arnold Schwarzenegger has a big one. Donald Trump has a small one. And Madonna doesn’t have one at all. What is it?',
        "answer": 'Last name',
        "aliases": [],
    },
    {
        "clue": 'What gets longer if pulled, fits snuggly between breasts, slides neatly into a hole, chokes people when used incorrectly, and works really well when jerked?',
        "answer": 'A seat belt',
        "aliases": ['seat belt'],
    },
    {
        "clue": 'What does every woman have that starts with ‘V’ and that she can use to get whatever she wants?',
        "answer": 'Voice',
        "aliases": [],
    },
    {
        "clue": 'A cow has four of them but a woman has just two. What is it?',
        "answer": 'Legs',
        "aliases": [],
    },
    {
        "clue": 'It’s fun to do but you hate knowing your parents do it too. What is it?',
        "answer": 'Facebook',
        "aliases": [],
    },
    {
        "clue": 'What is more rewarding when it’s long and hard?',
        "answer": 'A college education',
        "aliases": ['college education'],
    },
    {
        "clue": 'What’s white, sticky, and better to spit than to swallow?',
        "answer": 'Toothpaste',
        "aliases": [],
    },
    {
        "clue": 'It starts with the letter “P” and ends with “O.R.N”. I play a major role in the film industry. What am I?',
        "answer": 'Popcorn',
        "aliases": [],
    },
    {
        "clue": 'I work with briefs and I’m amazing when using my mouth. What am I?',
        "answer": 'A lawyer',
        "aliases": ['lawyer'],
    },
    {
        "clue": 'What are the two most important holes in a woman?',
        "answer": 'Nostrils',
        "aliases": [],
    },
    {
        "clue": 'You turn me on when you fiddle with my knobs. You have to change positions sometimes to improve.',
        "answer": 'Radio',
        "aliases": [],
    },
    {
        "clue": 'After you turn me on, I get hot. I’m of no use until you screw me. If I’m not in tight, I could fall out.',
        "answer": 'Lightbulb',
        "aliases": [],
    },
    {
        "clue": 'If you see me in bed, you whack me off. The bigger I am, the louder you’ll scream.',
        "answer": 'Spider',
        "aliases": [],
    },
    {
        "clue": 'If you hammer me, I’ll throb. If I’m points up, the answer is ‘Yes’. If I’m points down, the answer is ‘No’.',
        "answer": 'Magic 8-Ball',
        "aliases": [],
    },
    {
        "clue": 'I’m spread before I’m eaten. Your tongue gets me off. People sometimes lick my nuts.',
        "answer": 'Peanut butter',
        "aliases": [],
    },
    {
        "clue": 'I assist an erection. Sometimes big balls hang from me. I’m called a swinger.',
        "answer": 'Crane',
        "aliases": [],
    },
    {
        "clue": 'Over 1,000 people went down on me. I wasn’t maiden for long. A big hard thing ripped me open.',
        "answer": 'Titanic',
        "aliases": [],
    },
    {
        "clue": 'When I go in, I can produce pain. I cause you to spit and ask that you don’t swallow. I can fill your hole.',
        "answer": 'Dentist',
        "aliases": [],
    },
    {
        "clue": 'For a long time, it’s in and out. I discharge loads from my shaft. Everyone goes down on me.',
        "answer": 'Elevator',
        "aliases": [],
    },
    {
        "clue": 'I vibrate. I’m a lot of fun between your legs. I can handle two at a time.',
        "answer": 'Motorcycle',
        "aliases": [],
    },
    {
        "clue": 'I’m good at faking it. I get spread before I’m eaten. I sometimes come in the tub.',
        "answer": 'Margarine',
        "aliases": [],
    },
    {
        "clue": 'You push me in, pull me out, then tie me up when you’re done. I come in different colors.',
        "answer": 'Shoelace',
        "aliases": [],
    },
    {
        "clue": 'I’m big and thick. You wrap your hands around me to enjoy me. When I get hot, I’m ready to go.',
        "answer": 'Coffee mug',
        "aliases": [],
    },
    {
        "clue": 'I’m round and juicy, with a pit in the middle. People love to eat me, and sometimes I’m messy. What am I?',
        "answer": 'Peach',
        "aliases": [],
    },
    {
        "clue": 'I come in a variety of shapes and sizes. Some people prefer me warm, while others like me cold. What am I?',
        "answer": 'Pizza',
        "aliases": [],
    },
    {
        "clue": 'I start with a ‘P’ and end with ‘O-R-N’. I’m popular in the adult industry. What am I?',
        "answer": 'Popcorn',
        "aliases": [],
    },
    {
        "clue": 'I go in hard, come out soft, and you love to blow me. What am I?',
        "answer": 'Chewing gum',
        "aliases": [],
    },
    {
        "clue": 'You stick your poles inside me and tie me down to get me up. What am I?',
        "answer": 'A tent',
        "aliases": ['tent'],
    },
    {
        "clue": 'I have a long shaft and a round head. Men use me, but women blow me. What am I?',
        "answer": 'A flute',
        "aliases": ['flute'],
    },
    {
        "clue": 'I get bigger when you blow me, and I float. What am I?',
        "answer": 'A balloon',
        "aliases": ['balloon'],
    },
    {
        "clue": 'I’m long, thick, and full of seamen. What am I?',
        "answer": 'A submarine',
        "aliases": ['submarine'],
    },
    {
        "clue": 'You spread your legs to use me. What am I?',
        "answer": 'A pair of scissors',
        "aliases": ['pair of scissors'],
    },
    {
        "clue": 'The more you play with me, the harder I get. What am I?',
        "answer": 'A puzzle',
        "aliases": ['puzzle'],
    },
    {
        "clue": 'What four-letter word starts with ‘F’ and ends with ‘K’, and if you can’t have it, you use your hands?',
        "answer": 'Fork',
        "aliases": [],
    },
    {
        "clue": 'You blow me hard to make me come alive, but if you suck too much, I go limp. What am I?',
        "answer": 'A balloon',
        "aliases": ['balloon'],
    },
    {
        "clue": 'I go in dry and come out wet. What am I?',
        "answer": 'A tea bag',
        "aliases": ['tea bag'],
    },
    {
        "clue": 'I get longer when I’m pulled, fit perfectly between your breasts, and slide into a hole. What am I?',
        "answer": 'A seatbelt',
        "aliases": ['seatbelt'],
    },
    {
        "clue": 'The more you play with me, the wetter I get. What am I?',
        "answer": 'A bar of soap',
        "aliases": ['bar of soap'],
    },
    {
        "clue": 'You use your hands to move me up and down. What am I?',
        "answer": 'A pump',
        "aliases": ['pump'],
    },
    {
        "clue": 'I start with ‘C’, end in ‘T’, and have a ‘U’ and an ‘N’ in between. What am I?',
        "answer": 'A count',
        "aliases": ['count'],
    },
    {
        "clue": 'You tie me up to get me going, and when you’re done, you let me go. What am I?',
        "answer": 'A shoe',
        "aliases": ['shoe'],
    },
    {
        "clue": 'I’m round, sometimes hairy, and my white stuff shoots out fast. What am I?',
        "answer": 'A coconut',
        "aliases": ['coconut'],
    },
    {
        "clue": 'I come in different sizes, sometimes drip a little, and when you blow me, I feel better. What am I?',
        "answer": 'A nose',
        "aliases": ['nose'],
    },
    {
        "clue": 'The more you rub me, the hotter I get. What am I?',
        "answer": 'Two sticks making fire',
        "aliases": [],
    },
    {
        "clue": 'I get pulled out when things get hard. What am I?',
        "answer": 'A chair',
        "aliases": ['chair'],
    },
    {
        "clue": 'I can be long or short, men and women both love to blow me. What am I?',
        "answer": 'A whistle',
        "aliases": ['whistle'],
    },
    {
        "clue": 'What’s long, hard, and full of seamen?',
        "answer": 'A submarine',
        "aliases": ['submarine'],
    },
    {
        "clue": 'What’s better when it’s longer and gets cut when it’s too short?',
        "answer": 'A vacation',
        "aliases": ['vacation'],
    },
    {
        "clue": 'What’s the best part of your body to put into a pie?',
        "answer": 'Your teeth',
        "aliases": [],
    },
    {
        "clue": 'I can be flipped, licked, and sometimes get stuck between two buns. What am I?',
        "answer": 'A burger',
        "aliases": ['burger'],
    },
    {
        "clue": 'I get filled with cream and I’m delicious when you lick me. What am I?',
        "answer": 'A donut',
        "aliases": ['donut'],
    },
    {
        "clue": 'I go in one hole and come out another, and I’m always on your face. What am I?',
        "answer": 'A tongue',
        "aliases": ['tongue'],
    },
    {
        "clue": 'I’m a four-letter word that means “intercourse” but starts with ‘T’. What am I?',
        "answer": 'Talk',
        "aliases": [],
    },
    {
        "clue": 'You stick your meat inside of me and then eat me. What am I?',
        "answer": 'A sandwich',
        "aliases": ['sandwich'],
    },
    {
        "clue": 'I have a hole, a shaft, and I keep your balls in place. What am I?',
        "answer": 'A golf club',
        "aliases": ['golf club'],
    },
    {
        "clue": 'I’m long, you love me in your mouth, and sometimes I drip. What am I?',
        "answer": 'An ice cream cone',
        "aliases": ['ice cream cone'],
    },
    {
        "clue": 'I start with ‘S’, end with ‘X’, and I satisfy. What am I?',
        "answer": 'Snacks',
        "aliases": [],
    },
    {
        "clue": 'You slide me in and out, but if you do it too fast, I’ll overheat. What am I?',
        "answer": 'A credit card in a reader',
        "aliases": ['credit card in a reader'],
    },
    {
        "clue": 'You have to pull me out to use me, and sometimes I leave a mess behind. What am I?',
        "answer": 'A tissue',
        "aliases": ['tissue'],
    },
    {
        "clue": 'I get spread before I get eaten. What am I?',
        "answer": 'Butter',
        "aliases": [],
    },
    {
        "clue": 'I get shorter the more I stand tall. What am I?',
        "answer": 'A candle',
        "aliases": ['candle'],
    },
    {
        "clue": 'I’m long and round, I can get hard or soft, and people often chew on me. What am I?',
        "answer": 'A pencil',
        "aliases": ['pencil'],
    },
    {
        "clue": 'I’m stiff, I stand tall, and people use me when they’re feeling dirty. What am I?',
        "answer": 'A broom',
        "aliases": ['broom'],
    },
    {
        "clue": 'You can put your lips on me, but if you suck too hard, I’ll disappear. What am I?',
        "answer": 'A lollipop',
        "aliases": ['lollipop'],
    },
    {
        "clue": 'I get hot when you rub me, and I help you see in the dark. What am I?',
        "answer": 'A matchstick',
        "aliases": ['matchstick'],
    },
    {
        "clue": 'The harder I get hit, the better I sound. What am I?',
        "answer": 'A drum',
        "aliases": ['drum'],
    },
    {
        "clue": 'I start with ‘C’, end with ‘T’, and I’m something you can count on. What am I?',
        "answer": 'A count',
        "aliases": ['count'],
    },
    {
        "clue": 'I can be tied up, but I’m not a person. I can get licked, but I’m not food. What am I?',
        "answer": 'A shoe',
        "aliases": ['shoe'],
    },
    {
        "clue": 'The more you stroke me, the faster I go. What am I?',
        "answer": 'Aviolin',
        "aliases": [],
    },
    {
        "clue": 'I come in different sizes, and if you push the right buttons, I can bring you joy. What am I?',
        "answer": 'A remote control',
        "aliases": ['remote control'],
    },
    {
        "clue": 'You can hold me in your hand, I sometimes go off unexpectedly, and I often need a recharge. What am I?',
        "answer": 'A phone',
        "aliases": ['phone'],
    },
    {
        "clue": 'I go up but never come down. What am I?',
        "answer": 'Your age',
        "aliases": [],
    },
    {
        "clue": 'I’m shaped like a tube, I get squeezed, and I’m used in the morning. What am I?',
        "answer": 'Toothpaste',
        "aliases": [],
    },
    {
        "clue": 'You need to open your mouth to get the best out of me. What am I?',
        "answer": 'A joke',
        "aliases": ['joke'],
    },
    {
        "clue": 'The more you use me, the duller I get. What am I?',
        "answer": 'A knife',
        "aliases": ['knife'],
    },
    {
        "clue": 'People love to stick their heads inside me, but I’m not alive. What am I?',
        "answer": 'A sweater',
        "aliases": ['sweater'],
    },
    {
        "clue": 'I’m usually hung, sometimes round, and I help you see yourself better. What am I?',
        "answer": 'A mirror',
        "aliases": ['mirror'],
    },
    {
        "clue": 'You can put me between your legs, ride me hard, and still stay clean. What am I?',
        "answer": 'A bicycle',
        "aliases": ['bicycle'],
    },
    {
        "clue": 'I go in dry, come out wet, and the longer I stay in, the stronger I get. What am I?',
        "answer": 'A tea bag',
        "aliases": ['tea bag'],
    },
    {
        "clue": 'You need to turn me on before you can enjoy me. What am I?',
        "answer": 'A TV',
        "aliases": ['TV'],
    },
    {
        "clue": 'You squeeze me, twist me, and sometimes shake me to get me flowing. What am I?',
        "answer": 'A ketchup bottle',
        "aliases": ['ketchup bottle'],
    },
    {
        "clue": 'I have keys but open no locks. What am I?',
        "answer": 'A piano',
        "aliases": ['piano'],
    },
    {
        "clue": 'I can be dirty or clean, long or short, and people use me to express themselves. What am I?',
        "answer": 'A word',
        "aliases": ['word'],
    },
    {
        "clue": 'I’m a four-letter word that means “lift” and starts with ‘F’. What am I?',
        "answer": 'Fork',
        "aliases": [],
    },
    {
        "clue": 'I love getting blown, but I’m not alive. What am I?',
        "answer": 'A candle',
        "aliases": ['candle'],
    },
    {
        "clue": 'The more I’m handled, the thinner I get. What am I?',
        "answer": 'A bar of soap',
        "aliases": ['bar of soap'],
    },
    {
        "clue": 'I go between your lips, get sucked on, and eventually shrink. What am I?',
        "answer": 'A straw',
        "aliases": ['straw'],
    },
    {
        "clue": 'I have two nuts, a long shaft, and I get hammered all the time. What am I?',
        "answer": 'A bolt',
        "aliases": ['bolt'],
    },
    {
        "clue": 'I love getting stretched, but if you pull too hard, I might snap. What am I?',
        "answer": 'A rubber band',
        "aliases": ['rubber band'],
    },
    {
        "clue": 'I get wet before you do, and I’m usually the first thing you touch when you get in. What am I?',
        "answer": 'A shower handle',
        "aliases": ['shower handle'],
    },
    {
        "clue": 'I come in different sizes, I get stuffed often, and I protect what’s inside. What am I?',
        "answer": 'An envelope',
        "aliases": ['envelope'],
    },
    {
        "clue": 'I start soft, but you can make me rock hard. The longer you play with me, the better I get. What am I?',
        "answer": 'Clay',
        "aliases": [],
    },
    {
        "clue": 'I have a head, but I can’t think. I get banged to work properly. What am I?',
        "answer": 'A nail',
        "aliases": ['nail'],
    },
    {
        "clue": 'I’m big when I’m young, but small when I’m old. People love to blow me. What am I?',
        "answer": 'A candle',
        "aliases": ['candle'],
    },
    {
        "clue": 'I have a tip, but I’m not alive. I come in different colors and fit nicely in your hand. What am I?',
        "answer": 'A crayon',
        "aliases": ['crayon'],
    },
    {
        "clue": 'I’m made to be ridden, but I don’t go anywhere. If you handle me wrong, I’ll make you sore. What am I?',
        "answer": 'An exercise bike',
        "aliases": ['exercise bike'],
    },
    {
        "clue": 'You put your meat inside me before enjoying me. What am I?',
        "answer": 'A sandwich',
        "aliases": ['sandwich'],
    },
    {
        "clue": 'I’m made to be used over and over, but if I’m too full, I might leak. What am I?',
        "answer": 'A water bottle',
        "aliases": ['water bottle'],
    },
    {
        "clue": 'I get inserted, but I’m not alive. I vibrate sometimes and help you feel things better. What am I?',
        "answer": 'An electric toothbrush',
        "aliases": ['electric toothbrush'],
    },
    {
        "clue": 'You grab my stick and give me a good whack to send me flying. What am I?',
        "answer": 'A golf ball',
        "aliases": ['golf ball'],
    },
    {
        "clue": 'I get licked before I get stuck, but once I’m in, I do my job. What am I?',
        "answer": 'A stamp',
        "aliases": ['stamp'],
    },
    {
        "clue": 'You wrap your hands around me, and I help you go up and down smoothly. What am I?',
        "answer": 'A jump rope',
        "aliases": ['jump rope'],
    },
    {
        "clue": 'I go in empty and come out full, and I’m always in your pants. What am I?',
        "answer": 'A wallet',
        "aliases": ['wallet'],
    },
    {
        "clue": 'I can be long or short, thick or thin. I get stroked a lot to make things appear. What am I?',
        "answer": 'A paintbrush',
        "aliases": ['paintbrush'],
    },
    {
        "clue": 'You use your hands to open me up, and once inside, you find things you love. What am I?',
        "answer": 'A book',
        "aliases": ['book'],
    },
    {
        "clue": 'I’m held in your hands, used between your legs, and help you finish strong. What am I?',
        "answer": 'A bicycle handlebar',
        "aliases": ['bicycle handlebar'],
    },
    {
        "clue": 'I can be juicy, firm, or soft, and people love squeezing me. What am I?',
        "answer": 'A peach',
        "aliases": ['peach'],
    },
    {
        "clue": 'I can be long, round, and full of holes, and I get wet before you use me. What am I?',
        "answer": 'A sponge',
        "aliases": ['sponge'],
    },
    {
        "clue": 'I love getting rubbed the right way, and if you do it well, I’ll give you something special. What am I?',
        "answer": 'A genie lamp',
        "aliases": ['genie lamp'],
    },
    {
        "clue": 'I can be big or small, round or flat, but no matter what, I always get laid. What am I?',
        "answer": 'A carpet',
        "aliases": ['carpet'],
    },
    {
        "clue": 'People take me to bed, hold me tight, and love me when I’m soft. What am I?',
        "answer": 'A pillow',
        "aliases": ['pillow'],
    },
    {
        "clue": 'I have a lot of curves, and when you go down on me, I take you for a wild ride. What am I?',
        "answer": 'A rollercoaster',
        "aliases": ['rollercoaster'],
    },
    {
        "clue": 'The more you bang me, the louder I get. What am I?',
        "answer": 'A drum',
        "aliases": ['drum'],
    },
    {
        "clue": 'You stick me in tight places, wiggle me around, and pull me out wet. What am I?',
        "answer": 'A Q-tip',
        "aliases": ['Q-tip'],
    },
    {
        "clue": 'I come in a box, you use your fingers on me, and I make things come to life. What am I?',
        "answer": 'A remote',
        "aliases": ['remote'],
    },
    {
        "clue": 'I’m wet and slippery, and you use me to slide in. What am I?',
        "answer": 'Soap',
        "aliases": [],
    },
    {
        "clue": 'You wrap your lips around me and blow till I’m full. What am I?',
        "answer": 'A balloon',
        "aliases": ['balloon'],
    },
    {
        "clue": 'I buzz when I’m turned on and go between your legs. What am I?',
        "answer": 'A razor',
        "aliases": ['razor'],
    },
    {
        "clue": 'I start off soft, get hot and sticky, and end up in your mouth. What am I?',
        "answer": 'A marshmallow',
        "aliases": ['marshmallow'],
    },
    {
        "clue": 'The harder you ride me, the more I whine. What am I?',
        "answer": 'A treadmill',
        "aliases": ['treadmill'],
    },
    {
        "clue": 'I’m always getting stroked, sometimes wet, and used for pleasure. What am I?',
        "answer": 'A paintbrush',
        "aliases": ['paintbrush'],
    },
    {
        "clue": 'You blow me, I puff. You suck me, I die. What am I?',
        "answer": 'A cigarette',
        "aliases": ['cigarette'],
    },
    {
        "clue": 'I’m round, I roll, and I love getting played with. What am I?',
        "answer": 'A bowling ball',
        "aliases": ['bowling ball'],
    },
    {
        "clue": 'You pull me out fast, and I’ll spray everywhere. What am I?',
        "answer": 'A champagne bottle',
        "aliases": ['champagne bottle'],
    },
    {
        "clue": 'You lick me to the center, and I leave a creamy surprise. What am I?',
        "answer": 'A lollipop',
        "aliases": ['lollipop'],
    },
    {
        "clue": 'The more you work me, the more I moan. What am I?',
        "answer": 'A violin',
        "aliases": ['violin'],
    },
    {
        "clue": 'I’m long, get stuck in cracks, and you wiggle me till it feels better. What am I?',
        "answer": 'A back scratcher',
        "aliases": ['back scratcher'],
    },
    {
        "clue": 'I’m hot, juicy, and you can’t wait to sink your teeth into me. What am I?',
        "answer": 'A burger',
        "aliases": ['burger'],
    },
    {
        "clue": 'You grip me tight, ride me hard, and scream when I go too fast. What am I?',
        "answer": 'A rollercoaster',
        "aliases": ['rollercoaster'],
    },
    {
        "clue": 'You unzip me when things get hot. What am I?',
        "answer": 'Your pants',
        "aliases": [],
    },

]


# ==========================================================
# CLUE BANK VALIDATION
# ==========================================================

def validate_clue_bank() -> None:
    """
    Validate the clue bank when this module is loaded.

    This catches accidental malformed clues during development.
    """

    if len(DIRTY_MINDS_CLUES) < 100:
        raise RuntimeError(
            "Dirty Minds clue bank must contain at least 100 clues."
        )

    for index, clue in enumerate(DIRTY_MINDS_CLUES, start=1):

        if not isinstance(clue, dict):
            raise RuntimeError(
                f"Dirty Minds clue #{index} is not a dictionary."
            )

        if not clue.get("clue"):
            raise RuntimeError(
                f"Dirty Minds clue #{index} has no clue text."
            )

        if not clue.get("answer"):
            raise RuntimeError(
                f"Dirty Minds clue #{index} has no answer."
            )

        if "aliases" not in clue:
            clue["aliases"] = []

        if not isinstance(clue["aliases"], list):
            raise RuntimeError(
                f"Dirty Minds clue #{index} aliases must be a list."
            )


validate_clue_bank()


# ==========================================================
# TEXT NORMALIZATION
# ==========================================================

def normalize_answer(value: Any) -> str:
    """
    Normalize an answer for comparison.

    Examples:
        "A Toothbrush!" -> "toothbrush"
        "TOOTH BRUSH"  -> "toothbrush"
        "the pillow"   -> "pillow"
    """

    if value is None:
        return ""

    text = str(value).strip().lower()

    # Remove punctuation.
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text).strip()

    # Remove common leading articles.
    text = re.sub(
        r"^(a|an|the)\s+",
        "",
        text,
    )

    # Remove spaces for comparison.
    return text.replace(" ", "")


def _build_answer_keys(
    clue: dict[str, Any],
) -> set[str]:
    """
    Build all accepted normalized answers for a clue.
    """

    keys = {
        normalize_answer(
            clue.get("answer", "")
        ),
    }

    for alias in clue.get("aliases", []):
        normalized = normalize_answer(alias)

        if normalized:
            keys.add(normalized)

    return {
        key
        for key in keys
        if key
    }


def answer_is_correct(
    clue: dict[str, Any],
    answer: str,
) -> bool:
    """
    Check a submitted answer against the clue.
    """

    submitted = normalize_answer(answer)

    if not submitted:
        return False

    return submitted in _build_answer_keys(clue)


# ==========================================================
# GAME STATE
# ==========================================================

def create_dirty_minds_state() -> dict[str, Any]:
    """
    Create a brand-new Dirty Minds state.
    """

    return {
        "status": "waiting",

        "round": 0,
        "total_rounds": TOTAL_ROUNDS,

        # Selected clues for this game.
        "rounds": [],

        # Current clue.
        "current_clue": "",
        "current_answer": "",

        # Submitted answers.
        #
        # Key:
        #   player_key
        #
        # Value:
        #   {
        #       "answer": "...",
        #       "correct": True/False,
        #       "submitted_at": timestamp
        #   }
        #
        # This remains server-side.
        "answers": {},

        "revealed": False,

        "round_winner": None,

        "round_started_at": None,

        # Results become available only after reveal.
        "round_results": [],

        # Final winner.
        "winner": None,

        "game_started_at": None,
        "game_finished_at": None,
    }


# ==========================================================
# ROUND CREATION
# ==========================================================

def _select_rounds() -> list[dict[str, Any]]:
    """
    Randomly select the clues for a game.
    """

    count = min(
        TOTAL_ROUNDS,
        len(DIRTY_MINDS_CLUES),
    )

    selected = random.sample(
        DIRTY_MINDS_CLUES,
        count,
    )

    # Copy dictionaries so the original clue bank
    # can never be modified accidentally.
    return [
        {
            "clue": item["clue"],
            "answer": item["answer"],
            "aliases": list(
                item.get("aliases", [])
            ),
        }
        for item in selected
    ]


def _load_current_round(room) -> None:
    """
    Load the current round into the room state.
    """

    state = room.state

    round_number = int(
        state.get("round", 0)
    )

    rounds = state.get(
        "rounds",
        []
    )

    if round_number < 1:
        raise ValueError(
            "Invalid round number."
        )

    if round_number > len(rounds):
        raise ValueError(
            "Round does not exist."
        )

    current = rounds[
        round_number - 1
    ]

    state["current_clue"] = current["clue"]

    state["current_answer"] = current["answer"]

    state["answers"] = {}

    state["revealed"] = False

    state["round_winner"] = None

    state["round_results"] = []

    state["round_started_at"] = time.time()

    room.touch()


# ==========================================================
# START GAME
# ==========================================================

def start_game(room) -> dict[str, Any]:
    """
    Start or restart a Dirty Minds game.

    Host validation should be performed by the Flask route.
    """

    if room.player_count() < room.min_players:
        raise ValueError(
            f"At least {room.min_players} players are required."
        )

    rounds = _select_rounds()

    room.state = create_dirty_minds_state()

    room.state["status"] = "playing"

    room.state["round"] = 1

    room.state["total_rounds"] = len(rounds)

    room.state["rounds"] = rounds

    room.state["game_started_at"] = time.time()

    room.started = True

    room.finished = False

    room.winner_id = None

    room.reset_scores()

    _load_current_round(room)

    return public_room_state(room)


# ==========================================================
# SUBMIT ANSWER
# ==========================================================

def submit_answer(
    room,
    player_key: str,
    answer: str,
) -> dict[str, Any]:
    """
    Submit one answer for the current round.

    Each player may submit only once per round.
    """

    player = room.get_player_by_key(
        player_key
    )

    if not player:
        raise ValueError(
            "Player is not in this game."
        )

    state = room.state

    if state.get("status") != "playing":
        raise ValueError(
            "This round is not accepting answers."
        )

    if state.get("revealed"):
        raise ValueError(
            "The answer has already been revealed."
        )

    answer = str(
        answer or ""
    ).strip()

    if not answer:
        raise ValueError(
            "Please enter an answer."
        )

    if len(answer) > 100:
        raise ValueError(
            "Answer is too long."
        )

    answers = state.setdefault(
        "answers",
        {}
    )

    if player_key in answers:
        raise ValueError(
            "You already submitted an answer this round."
        )

    round_number = int(
        state.get("round", 0)
    )

    rounds = state.get(
        "rounds",
        []
    )

    if (
        not round_number
        or round_number > len(rounds)
    ):
        raise ValueError(
            "Invalid current round."
        )

    clue = rounds[
        round_number - 1
    ]

    answers[player_key] = {
        "answer": answer,
        "correct": None,
        "result": None,
        "points": 0.0,
        "graded": False,
        "submitted_at": time.time(),
    }

    room.touch()

    return {
        "success": True,
        "submitted": True,
        "correct": None,
        "message": "✅ Answer submitted. The host will grade it after the reveal.",
        "state": public_room_state(
            room,
            player_key=player_key,
        ),
    }


# ==========================================================
# REVEAL ROUND
# ==========================================================

def reveal_round(room) -> dict[str, Any]:
    """Reveal the answer and expose all submitted answers.

    Scoring is intentionally NOT automatic. The host grades each
    submitted answer as correct (1), partial (0.5), or wrong (0).
    """
    state = room.state
    if state.get("status") != "playing":
        raise ValueError("This round is not active.")
    if state.get("revealed"):
        return public_room_state(room)

    round_number = int(state.get("round", 0))
    rounds = state.get("rounds", [])
    if round_number < 1 or round_number > len(rounds):
        raise ValueError("Invalid current round.")

    results = []
    answers = state.get("answers", {})
    for player_key, submission in answers.items():
        player = room.get_player_by_key(player_key)
        if not player:
            continue
        results.append({
            "player_key": player_key,
            "name": player.get("name", "Player"),
            "answer": submission.get("answer", ""),
            "result": submission.get("result"),
            "points": float(submission.get("points", 0.0)),
            "graded": bool(submission.get("graded", False)),
        })

    submitted_keys = set(answers.keys())
    for player in room.players.values():
        key = player.get("player_key")
        if key in submitted_keys:
            continue
        results.append({
            "player_key": key,
            "name": player.get("name", "Player"),
            "answer": "",
            "result": "wrong",
            "points": 0.0,
            "graded": True,
            "did_not_answer": True,
        })

    state["revealed"] = True
    state["status"] = "revealed"
    state["round_results"] = results
    room.touch()
    return public_room_state(room)


# ==========================================================
# GRADE ANSWER
# ==========================================================

def grade_answer(room, host_player_key: str, target_player_key: str, grade: str) -> dict[str, Any]:
    """Host grades one submitted answer: correct=1, partial=0.5, wrong=0."""
    host = room.get_player_by_key(host_player_key)
    if not host or not host.get("host", False):
        raise ValueError("Only the host can grade answers.")

    state = room.state
    if not state.get("revealed") or state.get("status") != "revealed":
        raise ValueError("Reveal the round before grading answers.")

    if grade not in {"correct", "partial", "wrong"}:
        raise ValueError("Invalid grade.")

    submission = state.get("answers", {}).get(target_player_key)
    player = room.get_player_by_key(target_player_key)
    if not submission or not player:
        raise ValueError("Submitted answer not found.")

    if submission.get("graded"):
        raise ValueError("That answer has already been graded.")

    points = {"correct": 1.0, "partial": 0.5, "wrong": 0.0}[grade]
    submission["result"] = grade
    submission["points"] = points
    submission["correct"] = grade == "correct"
    submission["graded"] = True

    # Dirty Minds supports half-points.  The generic GameRoom score helper
    # converts points to int, which would turn 0.5 into 0.  Keep the score
    # directly on the player as a float so both +1 and +0.5 are preserved.
    current_score = float(player.get("score", 0) or 0)
    player["score"] = current_score + points
    room.touch()

    # Rebuild visible results and determine the round winner.
    results = []
    best = -1.0
    winners = []
    for key, sub in state.get("answers", {}).items():
        pl = room.get_player_by_key(key)
        if not pl:
            continue
        pts = float(sub.get("points", 0.0))
        results.append({
            "player_key": key,
            "name": pl.get("name", "Player"),
            "answer": sub.get("answer", ""),
            "result": sub.get("result"),
            "points": pts,
            "graded": bool(sub.get("graded", False)),
        })
        if sub.get("graded"):
            if pts > best:
                best = pts; winners = [pl]
            elif pts == best:
                winners.append(pl)
    if best > 0 and winners:
        state["round_winner"] = winners[0]["user_id"] if len(winners) == 1 else None
    state["round_results"] = results
    room.touch()
    return {"success": True, "graded": True, "grade": grade, "points": points, "state": public_room_state(room, player_key=host_player_key)}

# ==========================================================
# NEXT ROUND
# ==========================================================

def next_round(room) -> dict[str, Any]:
    """
    Advance to the next round.

    Host-only validation should be performed by the Flask route.
    """

    state = room.state

    status = state.get(
        "status"
    )

    if status not in {
        "playing",
        "revealed",
    }:
        raise ValueError(
            "The game is not ready for the next round."
        )

    if status == "revealed":
        # Do not trap the host on the reveal screen. Any answer the host
        # leaves ungraded is treated as 0 points when advancing. Answers
        # that were explicitly graded keep their awarded points.
        for submission in state.get("answers", {}).values():
            if not submission.get("graded", False):
                submission["result"] = "wrong"
                submission["points"] = 0.0
                submission["correct"] = False
                submission["graded"] = True

    current_round = int(
        state.get("round", 0)
    )

    total_rounds = int(
        state.get(
            "total_rounds",
            TOTAL_ROUNDS,
        )
    )

    if current_round >= total_rounds:
        return finish_game(room)

    state["round"] = (
        current_round + 1
    )

    _load_current_round(room)

    state["status"] = "playing"

    room.touch()

    return public_room_state(room)


# ==========================================================
# FINISH GAME
# ==========================================================

def finish_game(room) -> dict[str, Any]:
    """
    Finish the game and determine the winner.
    """

    state = room.state

    state["status"] = "finished"

    state["revealed"] = True

    state["game_finished_at"] = time.time()

    # Sort highest score first.
    players = sorted(
        room.players.values(),
        key=lambda player: (
            float(player.get("score", 0) or 0),
            -float(
                player.get(
                    "joined_at",
                    0,
                )
            ),
        ),
        reverse=True,
    )

    winner = None

    if players:

        top_score = float(players[0].get("score", 0) or 0)

        # Tie handling.
        tied = [
            player
            for player in players
            if float(player.get("score", 0) or 0) == top_score
        ]

        if len(tied) == 1:

            winner = {
                "name": tied[0].get(
                    "name",
                    "Player",
                ),
                "score": top_score,
            }

            room.winner_id = tied[0][
                "user_id"
            ]

        else:

            winner = {
                "name": "Tie Game",
                "score": top_score,
                "players": [
                    player.get(
                        "name",
                        "Player",
                    )
                    for player in tied
                ],
            }

            room.winner_id = None

    state["winner"] = winner

    room.finished = True

    room.touch()

    return public_room_state(room)


# ==========================================================
# RESET GAME
# ==========================================================

def reset_game(room) -> dict[str, Any]:
    """
    Reset a Dirty Minds room back to waiting.

    Useful if the host wants to start a completely new game.
    """

    room.state = create_dirty_minds_state()

    room.started = False

    room.finished = False

    room.winner_id = None

    room.reset_scores()

    room.touch()

    return public_room_state(room)


# ==========================================================
# PLAYER-SPECIFIC INFORMATION
# ==========================================================

def _player_submission(
    room,
    player_key: str | None,
) -> dict[str, Any] | None:
    """
    Get the current player's submission.
    """

    if not player_key:
        return None

    return room.state.get(
        "answers",
        {}
    ).get(
        player_key
    )


# ==========================================================
# PUBLIC GAME STATE
# ==========================================================

def public_room_state(
    room,
    player_key: str | None = None,
) -> dict[str, Any]:
    """
    Return information safe to send to a browser.

    IMPORTANT:
    The correct answer is hidden until the round is revealed.
    """

    state = room.state

    status = state.get(
        "status",
        "waiting",
    )

    revealed = bool(
        state.get(
            "revealed",
            False,
        )
    )

    current_answer = ""

    if revealed:
        current_answer = state.get(
            "current_answer",
            "",
        )

    submission = _player_submission(
        room,
        player_key,
    )

    my_submitted = (
        submission is not None
    )

    my_correct = None
    my_result = None
    my_points = 0.0
    if submission is not None and revealed and submission.get("graded"):
        my_correct = bool(submission.get("correct", False))
        my_result = submission.get("result")
        my_points = float(submission.get("points", 0.0))

    # Build player list without exposing:
    #
    #   - Telegram user IDs
    #   - player keys
    #   - internal timestamps
    #
    players = []

    for player in room.players.values():

        players.append(
            {
                "name": player.get(
                    "name",
                    "Player",
                ),
                "score": float(player.get("score", 0) or 0),
                "host": bool(
                    player.get(
                        "host",
                        False,
                    )
                ),
            }
        )

    result = {
        "room_id": room.room_id,

        "game_id": room.game_id,

        "game_name": room.game_name,

        "status": status,

        "round": int(
            state.get(
                "round",
                0,
            )
        ),

        "total_rounds": int(
            state.get(
                "total_rounds",
                TOTAL_ROUNDS,
            )
        ),

        "clue": state.get(
            "current_clue",
            "",
        ),

        # Answer remains hidden until reveal.
        "answer": current_answer,

        "revealed": revealed,

        "player_count": room.player_count(),

        "max_players": room.max_players,

        "min_players": room.min_players,

        "players": players,

        "submitted_count": len(
            state.get(
                "answers",
                {},
            )
        ),

        "my_submitted": my_submitted,

        "my_correct": my_correct,
        "my_result": my_result,
        "my_points": my_points,
        "round_winner": None,
        "submissions": [],

        "round_results": [],

        "winner": state.get(
            "winner"
        ),

        "started": bool(
            room.started
        ),

        "finished": bool(
            room.finished
        ),

        "is_host": False,

        "can_start": False,

        "can_reveal": False,

        "can_next": False,
    }

    # ======================================================
    # CURRENT PLAYER HOST STATUS
    # ======================================================

    if player_key:

        player = room.get_player_by_key(
            player_key
        )

        if player:

            result["is_host"] = bool(
                player.get(
                    "host",
                    False,
                )
            )

    # ======================================================
    # HOST CONTROLS
    # ======================================================

    result["can_start"] = (
        result["is_host"]
        and status in {
            "waiting",
            "finished",
        }
        and room.player_count()
        >= room.min_players
    )

    result["can_reveal"] = (
        result["is_host"]
        and status == "playing"
        and not revealed
    )

    result["can_next"] = (
        result["is_host"]
        and status == "revealed"
        and all(item.get("graded", False) for item in state.get("answers", {}).values())
    )

    # Only the host may see submitted answers before grading is complete.
    if result["is_host"] and status == "revealed":
        result["submissions"] = [
            {
                "player_key": key,
                "name": room.get_player_by_key(key).get("name", "Player") if room.get_player_by_key(key) else "Player",
                "answer": sub.get("answer", ""),
                "result": sub.get("result"),
                "points": float(sub.get("points", 0.0)),
                "graded": bool(sub.get("graded", False)),
            }
            for key, sub in state.get("answers", {}).items()
            if room.get_player_by_key(key)
        ]

    # ======================================================
    # REVEAL INFORMATION
    # ======================================================

    if revealed:

        result["round_winner"] = state.get(
            "round_winner"
        )

        result["round_results"] = list(
            state.get(
                "round_results",
                [],
            )
        )

    return result


# ==========================================================
# UTILITY FUNCTIONS
# ==========================================================

def get_current_clue(
    room,
) -> dict[str, Any] | None:
    """
    Return the current clue internally.

    This should NOT be sent directly to the browser because
    it contains the answer.
    """

    state = room.state

    round_number = int(
        state.get(
            "round",
            0,
        )
    )

    rounds = state.get(
        "rounds",
        []
    )

    if round_number < 1:
        return None

    if round_number > len(rounds):
        return None

    return rounds[
        round_number - 1
    ]


def get_correct_answer(
    room,
) -> str:
    """
    Get the correct answer internally.
    """

    return str(
        room.state.get(
            "current_answer",
            "",
        )
    )


def player_has_submitted(
    room,
    player_key: str,
) -> bool:
    """
    Check whether a player has submitted an answer
    for the current round.
    """

    if not player_key:
        return False

    return player_key in room.state.get(
        "answers",
        {},
    )


def all_players_submitted(
    room,
) -> bool:
    """
    Return True when every player has submitted.

    Returns False when the room has no players.
    """

    player_count = room.player_count()

    if player_count == 0:
        return False

    submitted_count = len(
        room.state.get(
            "answers",
            {},
        )
    )

    return submitted_count >= player_count


# ==========================================================
# CLUE BANK INFORMATION
# ==========================================================

def get_clue_count() -> int:
    """
    Return the number of clues currently available.
    """

    return len(DIRTY_MINDS_CLUES)


def get_random_clue() -> dict[str, Any]:
    """
    Return a random clue.

    Intended for internal use.
    """

    return random.choice(
        DIRTY_MINDS_CLUES
    )
