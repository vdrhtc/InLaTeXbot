<img src=https://cloud.githubusercontent.com/assets/3819012/21799537/1dab0e90-d733-11e6-88ab-76ebd37275c7.jpg /> 

Inline LaTeX bot for <a href=https://telegram.org>Telegram</a> messenger to send pictures with any LaTeX content to anyone from any device. Find it here: http://t.me/InLaTeXbot. 

##Description
This bot converts LaTeX expressions to .png images when called in inline mode (@inlatexbot \<your expression\>) and then shows you the image it has generated from your code. Everything happens live, so you can just gradually type in your expression and continuously monitor the result. When you are ready, click or tap the suggested picture to send it.

<img width=200 src=https://cloud.githubusercontent.com/assets/3819012/21800504/56bf38ec-d737-11e6-8b8b-e4e3b90d43ae.png />
<img width=200 src=https://cloud.githubusercontent.com/assets/3819012/21800503/56be411c-d737-11e6-8598-e43fb7126eb3.png />
<img width=200 src=https://cloud.githubusercontent.com/assets/3819012/21800505/56e9283c-d737-11e6-9195-1be0c2ca046c.png />


Additionally, this bot supports customization of the preamble used in the document into which your expression is inserted to generate the image:
```latex

\documentclass{article}
\usepackage[T1]{fontenc}
...
%You can modify everything above this comment
\begin{document}
<your expression goes here>
\end{document}
```
so that you can inlude the packages that you need or define own expressions and commands. The bot uses full installation of Texlive2016, so any package should be within its reach.

##Limitations
The expression length is limited by the length of the inline query to approximately 250 characters (despite the statement in the API docs that inline queries can span up to 512 characters)

The preamble length is currently limited by 4000 characters as it's not clear how long are the longest messages Telegram can process.

Bot should be currently online, so in case it's down it's either maintenance or some emergency. Also, feel free to open an issue if you find a bug or contact me <a href=http://t.me/vdrhtc>directly</a> in Telegram should you have any related questions.
