<img src=https://cloud.githubusercontent.com/assets/3819012/21799537/1dab0e90-d733-11e6-88ab-76ebd37275c7.jpg /> 

Inline LaTeX bot for Telegram messenger. 

Send pictures with any LaTeX content to anyone from any device!

##Description
This bot converts LaTeX expressions to .png images when called in inline mode (@inlatexbot \<your expression\>) and then shows you the image it has generated from your code. Everything happens live, so you can just gradually type in your expression and continuously monitor the result. When you are ready, click or tap the suggested picture to send it. 

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

