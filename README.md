# CS3103 Programming Assignment 1

## How to run the proxy
0. Check that Python 3.8 is available. At the point of writing this readme file, I have checked that Python 3.8.10 is available on both xcne1.comp.nus.edu.sg and xcne2.comp.nus.edu.sg.

1. Run the command `python3 proxy.py <port> <flag_telemetry> <filename of blacklist>`.


Note 1: The command above was tested on xcne2.comp.nus.edu.sg.

Note 2: In order to change the HTTP version used, you will need to comment out one of the HTTP_VERSION variable defined at the top of the proxy.py.

## Design

The design of the proxy is very similar to the descriptions given in the assignment sheet. After the browser establishes a connection with the proxy, the proxy will attempt to establish a connection with the server. If the connection has been established, the proxy will send a 200 OK response back to the client to inform him that the connection with the server has been established.

Thereafter, the proxy will simply forward packets between the client and the server. If HTTP/1.1 is used, the proxy will continue to forward packets until the connection has been idle for the duration of the timeout (5 seconds). Otherwise, the proxy will end the connection after the
first request-response pair.

## Comparison between HTTP/1.0 and HTTP/1.1

Output after accessing https://www.nus.edu.sg/ with HTTP/1.0:
```
Hostname: www.nus.edu.sg, Size: 78364 bytes, Time: 0.340 sec
Hostname: www.nus.edu.sg, Size: 10042 bytes, Time: 0.159 sec
Hostname: www.nus.edu.sg, Size: 3962 bytes, Time: 0.180 sec
Hostname: www.nus.edu.sg, Size: 3347 bytes, Time: 0.180 sec
Hostname: www.nus.edu.sg, Size: 10353 bytes, Time: 0.184 sec
Hostname: www.nus.edu.sg, Size: 6647 bytes, Time: 0.185 sec
Hostname: www.nus.edu.sg, Size: 3289 bytes, Time: 0.180 sec
Hostname: www.nus.edu.sg, Size: 7557 bytes, Time: 0.173 sec
Hostname: www.nus.edu.sg, Size: 38832 bytes, Time: 0.181 sec
Hostname: www.nus.edu.sg, Size: 3854 bytes, Time: 0.315 sec
Hostname: www.nus.edu.sg, Size: 3680 bytes, Time: 0.315 sec
Hostname: www.nus.edu.sg, Size: 5414 bytes, Time: 0.339 sec
Hostname: www.nus.edu.sg, Size: 34528 bytes, Time: 0.346 sec
Hostname: fonts.googleapis.com, Size: 3560 bytes, Time: 0.192 sec
Hostname: www.nus.edu.sg, Size: 4859 bytes, Time: 0.202 sec
Hostname: www.nus.edu.sg, Size: 3281 bytes, Time: 0.175 sec
Hostname: www.nus.edu.sg, Size: 3546 bytes, Time: 0.169 sec
Hostname: www.nus.edu.sg, Size: 3347 bytes, Time: 0.176 sec
Hostname: www.nus.edu.sg, Size: 3397 bytes, Time: 0.184 sec
Hostname: www.nus.edu.sg, Size: 21720 bytes, Time: 0.052 sec
Hostname: www.nus.edu.sg, Size: 5175 bytes, Time: 0.043 sec
Hostname: www.nus.edu.sg, Size: 6532 bytes, Time: 0.046 sec
Hostname: www.nus.edu.sg, Size: 4390 bytes, Time: 0.050 sec
Hostname: www.nus.edu.sg, Size: 4357 bytes, Time: 0.047 sec
Hostname: www.nus.edu.sg, Size: 26233 bytes, Time: 0.031 sec
Hostname: www.nus.edu.sg, Size: 81887 bytes, Time: 0.041 sec
Hostname: www.nus.edu.sg, Size: 3045 bytes, Time: 0.022 sec
Hostname: www.nus.edu.sg, Size: 16785 bytes, Time: 0.038 sec
Hostname: www.nus.edu.sg, Size: 51860 bytes, Time: 0.042 sec
Hostname: www.nus.edu.sg, Size: 3942 bytes, Time: 0.036 sec
Hostname: www.nus.edu.sg, Size: 4204 bytes, Time: 0.030 sec
Hostname: www.nus.edu.sg, Size: 3905 bytes, Time: 0.040 sec
Hostname: www.nus.edu.sg, Size: 5607 bytes, Time: 0.036 sec
Hostname: www.nus.edu.sg, Size: 3999 bytes, Time: 0.069 sec
Hostname: www.nus.edu.sg, Size: 4372 bytes, Time: 0.051 sec
Hostname: www.nus.edu.sg, Size: 491355 bytes, Time: 0.133 sec
Hostname: www.nus.edu.sg, Size: 528068 bytes, Time: 0.137 sec
Hostname: www.nus.edu.sg, Size: 3350 bytes, Time: 0.024 sec
Hostname: www.nus.edu.sg, Size: 78775 bytes, Time: 0.046 sec
Hostname: www.nus.edu.sg, Size: 110841 bytes, Time: 0.061 sec
Hostname: www.nus.edu.sg, Size: 108506 bytes, Time: 0.066 sec
Hostname: www.nus.edu.sg, Size: 84511 bytes, Time: 0.058 sec
Hostname: www.nus.edu.sg, Size: 63520 bytes, Time: 0.120 sec
Hostname: www.nus.edu.sg, Size: 54132 bytes, Time: 0.056 sec
Hostname: www.nus.edu.sg, Size: 61575 bytes, Time: 0.045 sec
Hostname: www.nus.edu.sg, Size: 50171 bytes, Time: 0.047 sec
Hostname: www.nus.edu.sg, Size: 25937 bytes, Time: 0.032 sec
Hostname: www.nus.edu.sg, Size: 3332 bytes, Time: 0.030 sec
Hostname: www.nus.edu.sg, Size: 38211 bytes, Time: 0.040 sec
Hostname: www.nus.edu.sg, Size: 56608 bytes, Time: 0.043 sec
Hostname: www.nus.edu.sg, Size: 12496 bytes, Time: 0.030 sec
Hostname: www.nus.edu.sg, Size: 12419 bytes, Time: 0.042 sec
Hostname: www.nus.edu.sg, Size: 2961 bytes, Time: 0.042 sec
Hostname: www.nus.edu.sg, Size: 72072 bytes, Time: 0.057 sec
Hostname: www.nus.edu.sg, Size: 6579 bytes, Time: 0.043 sec
Hostname: www.nus.edu.sg, Size: 10781 bytes, Time: 0.104 sec
Hostname: www.nus.edu.sg, Size: 21804 bytes, Time: 0.051 sec
Hostname: www.nus.edu.sg, Size: 21836 bytes, Time: 0.071 sec
Hostname: www.nus.edu.sg, Size: 21771 bytes, Time: 0.084 sec
Hostname: www.nus.edu.sg, Size: 21737 bytes, Time: 0.048 sec
Hostname: www.nus.edu.sg, Size: 21803 bytes, Time: 0.053 sec
Hostname: www.nus.edu.sg, Size: 21803 bytes, Time: 0.051 sec
Hostname: www.nus.edu.sg, Size: 6579 bytes, Time: 0.044 sec
Hostname: www.nus.edu.sg, Size: 4026 bytes, Time: 0.029 sec
Hostname: news.nus.edu.sg, Size: 36708 bytes, Time: 0.799 sec
Hostname: www.instagram.com, Size: 81064 bytes, Time: 5.049 sec
Hostname: stats.g.doubleclick.net, Size: 3075 bytes, Time: 5.028 sec
Hostname: www.google-analytics.com, Size: 24553 bytes, Time: 5.168 sec
Hostname: content.presspage.com, Size: 926544 bytes, Time: 5.321 sec
Hostname: content.presspage.com, Size: 1085165 bytes, Time: 5.350 sec
Hostname: content.presspage.com, Size: 1174809 bytes, Time: 5.415 sec
Hostname: content.presspage.com, Size: 1630648 bytes, Time: 5.485 sec
```
Output after accessing https://www.nus.edu.sg/ with HTTP/1.1:

```
Hostname: fonts.googleapis.com, Size: 3986 bytes, Time: 5.037 sec
Hostname: www.nus.edu.sg, Size: 353077 bytes, Time: 5.404 sec
Hostname: www.nus.edu.sg, Size: 198320 bytes, Time: 5.404 sec
Hostname: www.nus.edu.sg, Size: 204432 bytes, Time: 5.444 sec
Hostname: www.nus.edu.sg, Size: 596246 bytes, Time: 5.471 sec
Hostname: www.nus.edu.sg, Size: 214490 bytes, Time: 5.472 sec
Hostname: www.nus.edu.sg, Size: 846535 bytes, Time: 6.167 sec
Hostname: news.nus.edu.sg, Size: 36779 bytes, Time: 5.695 sec
Hostname: www.google-analytics.com, Size: 24435 bytes, Time: 5.521 sec
Hostname: www.instagram.com, Size: 84275 bytes, Time: 5.061 sec
Hostname: content.presspage.com, Size: 925529 bytes, Time: 5.281 sec
Hostname: content.presspage.com, Size: 1085850 bytes, Time: 5.324 sec
Hostname: content.presspage.com, Size: 1178013 bytes, Time: 5.460 sec
Hostname: content.presspage.com, Size: 1631124 bytes, Time: 5.449 sec
```

There are much fewer entries for HTTP/1.1 because of pipelining. This means that within each connection, there can be multiple request-response pairs.

