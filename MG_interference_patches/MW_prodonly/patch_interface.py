633,634c633,634
<                         likelihood[card] -= math.log(value)
<                         err_likelihood[card] += error / value
---
>                         likelihood[card] -= math.log(abs(value))
>                         err_likelihood[card] += error / abs(value)
