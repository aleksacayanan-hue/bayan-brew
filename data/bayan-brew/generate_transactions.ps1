$rnd = [System.Random]::new(20261001)
$out = Split-Path -Parent $MyInvocation.MyCommand.Path

$stores = @(
  @('ST01','Bayan Brew SM North','Quezon City','Metro Manila'),
  @('ST02','Bayan Brew Trinoma','Quezon City','Metro Manila'),
  @('ST03','Bayan Brew MOA','Pasay','Metro Manila'),
  @('ST04','Bayan Brew BGC High Street','Taguig','Metro Manila'),
  @('ST05','Bayan Brew Eastwood','Quezon City','Metro Manila'),
  @('ST06','Bayan Brew Ayala Cebu','Cebu City','Central Visayas'),
  @('ST07','Bayan Brew SM Davao','Davao City','Davao Region'),
  @('ST08','Bayan Brew Robinsons Iloilo','Iloilo City','Western Visayas'),
  @('ST09','Bayan Brew Marquee Mall','Angeles','Central Luzon'),
  @('ST10','Bayan Brew SM Baguio','Baguio','Cordillera')
)

$products = @(
  @('PR01','Classic Milk Tea','Milk Tea',89),
  @('PR02','Wintermelon Milk Tea','Milk Tea',89),
  @('PR03','Okinawa Milk Tea','Milk Tea',99),
  @('PR04','Taro Milk Tea','Milk Tea',109),
  @('PR05','Brown Sugar Fresh Milk','Signature',129),
  @('PR06','Matcha Latte','Latte',119),
  @('PR07','Coffee Jelly Milk Tea','Milk Tea',109),
  @('PR08','Fruit Tea Green Apple','Fruit Tea',79),
  @('PR09','Fruit Tea Passion','Fruit Tea',79),
  @('PR10','Cheese Foam Jasmine','Premium',139),
  @('PR11','Salted Cream Black Tea','Premium',129),
  @('PR12','Chocolate Oreo Smoothie','Smoothie',119),
  @('PR13','Mango Snow','Smoothie',129),
  @('PR14','Egg Pudding Add-on','Add-on',25),
  @('PR15','Pearl Add-on','Add-on',15)
)

$storeWeights = @{
  'ST01' = 1.0; 'ST02' = 1.0; 'ST03' = 1.4; 'ST04' = 1.4; 'ST05' = 1.0
  'ST06' = 1.15; 'ST07' = 1.15; 'ST08' = 1.0; 'ST09' = 1.0; 'ST10' = 1.0
}

function Get-BusinessMultiplier([datetime]$d) {
  $m = 1.0
  if ([int]$d.DayOfWeek -ge 5) { $m *= 1.35 }
  if ($d.Month -in 4, 5, 12) { $m *= 1.12 }
  return $m
}

function Pick-Store() {
  $total = 0.0
  foreach ($s in $stores) { $total += $storeWeights[$s[0]] }
  $roll = $rnd.NextDouble() * $total
  $acc = 0.0
  foreach ($s in $stores) {
    $acc += $storeWeights[$s[0]]
    if ($roll -le $acc) { return $s }
  }
  return $stores[-1]
}

$storeCsv = @('StoreID,StoreName,City,Region')
foreach ($s in $stores) { $storeCsv += ('"{0}","{1}","{2}","{3}"' -f $s[0], $s[1], $s[2], $s[3]) }
$storeCsv | Set-Content (Join-Path $out 'bayan-brew-stores.csv') -Encoding utf8

$prodCsv = @('ProductID,ProductName,Category,BasePriceSmall')
foreach ($p in $products) { $prodCsv += ('"{0}","{1}","{2}",{3}' -f $p[0], $p[1], $p[2], $p[3]) }
$prodCsv | Set-Content (Join-Path $out 'bayan-brew-products.csv') -Encoding utf8

$main = @($products | Where-Object { $_[2] -ne 'Add-on' })
$addons = @($products | Where-Object { $_[2] -eq 'Add-on' })

$tx = [System.Collections.Generic.List[string]]::new()
$tx.Add('OrderID,OrderDate,OrderTime,StoreID,ProductID,Size,Quantity,UnitPricePHP,LineRevenuePHP')

$orderSeq = 1
$start = [datetime]'2025-01-01'
$end = [datetime]'2025-09-30'

for ($d = $start; $d -le $end; $d = $d.AddDays(1)) {
  $nOrders = [int]($rnd.Next(45, 96) * (Get-BusinessMultiplier $d))
  for ($o = 0; $o -lt $nOrders; $o++) {
    $store = Pick-Store
    $sid = $store[0]
    $oid = 'ORD-{0}-{1:D5}' -f $d.ToString('yyyyMMdd'), $orderSeq
    $orderSeq++
    $hour = $rnd.Next(10, 22)
    $min = $rnd.Next(0, 60)

    $nLines = switch ($rnd.Next(0, 100)) {
      { $_ -lt 55 } { 1 }
      { $_ -lt 90 } { 2 }
      default { 3 }
    }

    for ($li = 0; $li -lt $nLines; $li++) {
      $p = $main[$rnd.Next(0, $main.Count)]
      $sizeRoll = $rnd.NextDouble()
      if ($sizeRoll -lt 0.25) { $size = 'Small'; $mult = 1.0 }
      elseif ($sizeRoll -lt 0.80) { $size = 'Medium'; $mult = 1.15 }
      else { $size = 'Large'; $mult = 1.3 }
      $qty = if ($rnd.NextDouble() -lt 0.92) { 1 } else { 2 }
      $unit = [math]::Round([double]$p[3] * $mult, 2)
      $rev = [math]::Round($unit * $qty, 2)
      $tx.Add(('"{0}","{1}","{2:D2}:{3:D2}","{4}","{5}","{6}",{7},{8},{9}' -f $oid, $d.ToString('yyyy-MM-dd'), $hour, $min, $sid, $p[0], $size, $qty, $unit, $rev))
    }

    if ($rnd.NextDouble() -lt 0.22) {
      $a = $addons[$rnd.Next(0, $addons.Count)]
      $unit = [double]$a[3]
      $tx.Add(('"{0}","{1}","{2:D2}:{3:D2}","{4}","{5}","N/A",1,{6},{6}' -f $oid, $d.ToString('yyyy-MM-dd'), $hour, $min, $sid, $a[0], $unit))
    }
  }
}

$tx | Set-Content (Join-Path $out 'bayan-brew-transactions.csv') -Encoding utf8
Write-Host ('Wrote {0} transaction lines.' -f ($tx.Count - 1))
