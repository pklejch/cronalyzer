# cronalyzer
Cronalyzer is a tool for analyzing and optimizing crontabs.

*It was my first Python project, so it is little rough around the edges. It is more like working prototype and there is a lot work to do.*

Features:
- Written in Python3, requires following modules: matplotlib, numpy, dominate, deap, collections, intervaltree and scoop.
- Reads crontabs and creates graphs and report.
- Using 3 attributes written in crontabs comments (duration, shift and weight) this tool will try to optimize crontabs by shifting tasks, so that all tasks won't run exactly at 00:00 at midnigth.
- Attributes in the crontabs are required for successful optimization. Duration specify how long will task run in seconds. Shift specify how far can be task shifted (in minutes). And weight specify how CPU heavy this task is (more weight = more CPU heavy). If attributes are not specified, default will be used. 
- Configuration file: config.conf
