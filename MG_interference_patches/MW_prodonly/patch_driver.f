421c421
<          cross = cross + perm_value_it(i,1)/(perm_error_it(i,1)+1d-99)
---
>          cross = cross + abs(perm_value_it(i,1))/(perm_error_it(i,1)+1d-99)
428c428
<            value = perm_value_it(j,1)/
---
>            value = abs(perm_value_it(j,1))/
474c474
<             if (data(i).ge.data(i-j)) then
---
>             if (abs(data(i)).ge.abs(data(i-j))) then
487c487
<          cross = cross + perm_value(i,1)
---
>          cross = cross + abs(perm_value(i,1))
492c492
<           tmp = perm_value(j,1)
---
>           tmp = abs(perm_value(j,1))
521c521
<             if (data(i).ge.data(i-j)) then
---
>             if (abs(data(i)).ge.abs(data(i-j))) then
