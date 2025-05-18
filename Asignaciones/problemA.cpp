#include <bits/stdc++.h>
//#######################
using namespace std;
typedef long long ll;
//########################

int main()
{
	int n_casos=0;
	cin>>n_casos;
	string words[n_casos];
	for(int i=0;i<n_casos;i++)
	{
		cin>>words[i];
	}
	
	for(int i=0;i<n_casos;i++)
	{
		words[i][words[i].size()-2]='i';
		words[i][words[i].size()-1]=' ';
	}
	for(int i=0;i<n_casos;i++)
	{
		cout<<words[i]<<endl;
	}
	
	return 0;
}
