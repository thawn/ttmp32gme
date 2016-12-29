package TTMp32Gme::LibraryHandler;

use strict;
use warnings;

use File::Basename qw(basename dirname);
use Data::Dumper;
use Path::Class;
use List::MoreUtils qw(uniq);
use Cwd;

use Image::Info qw(image_type);
use Music::Tag ( traditional => 1 );
use Music::Tag::MusicBrainz;
use Music::Tag::MP3;
use Music::Tag::OGG;
use MP3::Tag;

#use Music::Tag:Amazon; #needs developer key
#use Music::Tag:LyricsFetcher; #maybe use this in a future release?

use TTMp32Gme::Build::FileHandler;

require Exporter;
our @ISA = qw(Exporter);
our @EXPORT =
	qw(updateTableEntry put_file_online createLibraryEntry get_album_list get_album get_album_online updateAlbum deleteAlbum cleanupAlbum);

## private methods

sub oid_exist {
	my ( $oid, $dbh ) = @_;
	my @old_oids = map { @$_ }
		@{ $dbh->selectall_arrayref('SELECT oid FROM gme_library ORDER BY oid') };
	if ( grep( /^$oid$/, @old_oids ) ) {
		return 1;
	} else {
		return 0;
	}
}

sub newOID {
	my $dbh = $_[0];
	my $oid;
	my @old_oids =
		map { @$_ }
		@{ $dbh->selectall_arrayref('SELECT oid FROM gme_library ORDER BY oid DESC')
		};
	if (@old_oids) {
		if ( $old_oids[0] < 999 ) {

			#if we have free oids above the highest used oid, then use those
			$oid = $old_oids[0] + 1;
		} else {

			#if oid 999 is already in the database,
			#then look for oids freed by deleting old ones
			my %oid_test = map { $_ => 1 } @old_oids;
			my $new_oid = $old_oids[-1] + 1;
			while ( ( $new_oid < 1001 ) and ( $oid_test{$new_oid} ) ) {
				$new_oid++;
			}
			if ( $new_oid == 1000 ) {

				#we still have not found a free oid,
				#look for free oids below the default oid
				$new_oid = $old_oids[-1] - 1;
				while ( $new_oid gt 0 and $oid_test{$new_oid} ) {
					$new_oid -= 1;
				}
				if ( $new_oid > 1 ) {
					$oid = $new_oid;
				} else {
					error(
						'could not find a free oid.'
							. ' Try deleting oids from your library.',
						1
					);
				}
			} else {
				$oid = $new_oid;
			}
		}
	} else {
		$oid = 920;
	}
	return $oid;
}

sub writeToDatabase {
	my ( $table, $data, $dbh ) = @_;
	my @fields = sort keys %$data;
	my @values = @{$data}{@fields};
	my $query  = sprintf(
		"INSERT INTO $table (%s) VALUES (%s)",
		join( ", ", @fields ),
		join( ", ", map { '?' } @values )
	);
	my $qh = $dbh->prepare($query);
	$qh->execute(@values);
}

sub get_tracks {
	my ( $album, $dbh ) = @_;
	my $query =
		"SELECT * FROM tracks WHERE parent_oid=$album->{'oid'} ORDER BY track";
	my $tracks = $dbh->selectall_hashref( $query, 'track' );
	foreach my $track ( sort keys %{$tracks} ) {
		$album->{ 'track_' . $track } = $tracks->{$track};
	}
	return $album;
}

sub put_cover_online {
	my ( $album, $httpd ) = @_;
	if ( $album->{'picture_filename'} ) {
		my $picture_file = file( $album->{'path'}, $album->{'picture_filename'} );
		my $online_path = '/assets/images/' . $album->{'oid'} . '/' . $album->{'picture_filename'};
		put_file_online( $picture_file, $online_path, $httpd );
		return 1;
	} else {
		return 0;
	}
}

sub switchTracks {
	my ( $oid, $new_tracks, $dbh ) = @_;
	my $query = "SELECT * FROM tracks WHERE parent_oid=$oid ORDER BY track";
	my $tracks = $dbh->selectall_hashref( $query, 'track' );
	$dbh->do("DELETE FROM tracks WHERE parent_oid=$oid");
	foreach my $track ( sort keys %{$new_tracks} ) {
		$tracks->{$track}{'track'} = $new_tracks->{$track};
		writeToDatabase( 'tracks', $tracks->{$track}, $dbh );
	}
}

## public methods:

sub updateTableEntry {
	my ( $table, $keyname, $search_keys, $data, $dbh ) = @_;
	my @fields = sort keys %$data;
	my @values = @{$data}{@fields};
	my $qh     = $dbh->prepare(
		sprintf(
			'UPDATE %s SET %s=? WHERE %s',
			$table, join( "=?, ", @fields ), $keyname
		)
	);
	push( @values, @{$search_keys} );
	$qh->execute(@values);
	return !$dbh->errstr;
}

sub put_file_online {
	my ( $file, $online_path, $httpd ) = @_;
	my $file_data = $file->slurp();
	$httpd->reg_cb(
		$online_path => sub {
			my ( $httpd, $req ) = @_;
			$req->respond( { content => [ '', $file_data ] } );
		}
	);
	return 1;
}

sub createLibraryEntry {
	my ( $albumList, $dbh ) = @_;
	foreach my $album ( @{$albumList} ) {
		if ($album) {
			my $oid = newOID($dbh);
			my %albumData;
			my @trackData;
			my $pictureData;
			foreach my $fileId ( sort keys %{$album} ) {
				if ( $album->{$fileId} =~ /\.(mp3|ogg)$/i ) {

					#handle mp3 and ogg audio files
					my $info = Music::Tag->new( $album->{$fileId} );
					$info->get_tag( $album->{$fileId} );

					#fill in album info
					if ( !$albumData{'album_title'} && $info->album() ) {
						$albumData{'album_title'} = $info->album();
						$albumData{'path'}        = $albumData{'album_title'};
					}
					if ( !$albumData{'album_artist'} && $info->albumartist() ) {
						$albumData{'album_artist'} = $info->albumartist();
					} elsif ( !$albumData{'album_artist'} && $info->artist() ) {
						$albumData{'album_artist'} = $info->artist();
					}
					if ( !$albumData{'album_year'} && $info->year() ) {
						$albumData{'album_year'} = $info->get_year();
					}
					if ( !$albumData{'picture_filename'} && $info->picture_exists() ) {
						if ( $info->picture_filename() ) {
							$albumData{'picture_filename'} = $info->picture_filename();
						} elsif ( $info->picture() ) {
							my %pic = $info->picture();
							$pictureData = $pic{'_Data'};
							$albumData{'picture_filename'} = basename( $pic{'filename'} );
						}
					} elsif ( !$albumData{'picture_filename'}
						&& !$info->picture_exists()
						&& $album->{$fileId} =~ /\.mp3$/i )
					{
						#Music::Tag::MP3 is not always reliable when extracting the picture,
						#try to use MP3::Tag directly.
						my $mp3 = MP3::Tag->new( $album->{$fileId} );
						$mp3->get_tags();
						my $id3v2_tagdata = $mp3->{ID3v2};
						my $apic          = $id3v2_tagdata->get_frame("APIC");
						$pictureData = $$apic{'_Data'};
						my $mimetype = $$apic{'MIME type'};
						if ($mimetype) {
							$mimetype =~ s/.*\///;
							$albumData{'picture_filename'} = 'cover.' . $mimetype;
						} elsif ($pictureData) {
							my $imgType = image_type( \$pictureData );
							$albumData{'picture_filename'} = 'cover.' . $imgType;
						}
					}

					#fill in track info
					my %trackInfo = (
						'parent_oid' => $oid,
						'album'      => $info->album(),
						'artist'     => $info->artist(),
						'disc'       => $info->disc(),
						'duration'   => $info->duration(),
						'genre'      => $info->genre(),
						'lyrics'     => $info->lyrics(),
						'title'      => $info->title(),
						'track'      => $info->track(),
						'filename'   => $album->{$fileId},
					);
					push( @trackData, \%trackInfo );
				} elsif ( $album->{$fileId} =~ /\.(jpg|jpeg|tif|tiff|png|gif)$/i ) {

					#handle pictures
					open( my $file, '<', $album->{$fileId} );
					$pictureData = join( "", <$file> );
					close($file);
					$albumData{'picture_filename'} = basename( $album->{$fileId} );
				}
			}
			$albumData{'oid'}        = $oid;
			$albumData{'num_tracks'} = scalar(@trackData);
			if ( !$albumData{'album_title'} ) {
				$albumData{'path'}        = 'unknown';
				$albumData{'album_title'} = $albumData{'path'};
			}
			$albumData{'path'} = makeNewAlbumDir( $albumData{'path'} );
			if ( $albumData{'picture_filename'} and $pictureData ) {
				open(
					my $fh,
					'>',
					( file( $albumData{'path'}, $albumData{'picture_filename'} ) )
						->stringify
				);
				print $fh $pictureData;
				close($fh);
			}
			foreach my $track (@trackData) {
				$track->{'filename'} =
					moveToAlbum( $albumData{'path'}, $track->{'filename'} );
				writeToDatabase( 'tracks', $track, $dbh );
			}
			writeToDatabase( 'gme_library', \%albumData, $dbh );
		}
	}
	removeTempDir();
}

sub get_album_list {
	my ( $dbh, $httpd ) = @_;
	my @albumList;
	my $albums =
		$dbh->selectall_hashref( q( SELECT * FROM gme_library ORDER BY oid DESC ),
		'oid' );
	foreach my $oid ( sort keys %{$albums} ) {
		$albums->{$oid} = get_tracks( $albums->{$oid}, $dbh );
		put_cover_online( $albums->{$oid}, $httpd );
		push( @albumList, $albums->{$oid} );
	}
	return \@albumList;
}

sub get_album {
	my ( $oid, $dbh ) = @_;
	my $album =
		$dbh->selectrow_hashref( q( SELECT * FROM gme_library WHERE oid=? ),
		{}, $oid );
	$album = get_tracks( $album, $dbh );
	return $album;
}

sub get_album_online {
	my ( $oid, $httpd, $dbh ) = @_;
	my $album = get_album( $oid, $dbh );
	put_cover_online( $album, $httpd );
	return $album;
}

sub updateAlbum {
	my ( $postData, $dbh ) = @_;
	my $old_oid = $postData->{'old_oid'};
	delete( $postData->{'old_oid'} );
	if ( $old_oid != $postData->{'oid'} ) {
		if ( oid_exist( $old_oid, $dbh ) ) {
			return 0;
			$dbh->set_err( '',
				'Could not update album, oid already exists. Try a different oid.' );
		} else {
			for my $track ( grep /^track_/, keys %{$postData} ) {
				$postData->{$track}{'parent_oid'} = $postData->{'oid'};
			}
		}
	}
	my %new_tracks;
	for my $track ( sort grep /^track_/, keys %{$postData} ) {
		my $old_track = $track;
		$old_track =~ s/^track_//;
		$new_tracks{$old_track} = $postData->{$track}{'track'};
		delete( $postData->{$track}{'track'} );
		my %trackData = %{ $postData->{$track} };
		my @selectors = ( $old_oid, $old_track );
		updateTableEntry( 'tracks', 'parent_oid=? and track=?',
			\@selectors, \%trackData, $dbh );
		delete( $postData->{$track} );
	}
	switchTracks( $postData->{'oid'}, \%new_tracks, $dbh );
	my @selector = ($old_oid);
	updateTableEntry( 'gme_library', 'oid=?', \@selector, $postData, $dbh );
	return $postData->{'oid'};
}

sub deleteAlbum {
	my ( $oid, $httpd, $dbh ) = @_;
	my $albumData = $dbh->selectrow_hashref(
		q(SELECT path,picture_filename FROM gme_library WHERE oid=?),
		{}, $oid );
	if ( $albumData->{'picture_filename'} ) {
		$httpd->unreg_cb(
			'/assets/images/' . $oid . '/' . $albumData->{'picture_filename'} );
	}
	if ( remove_library_dir( $albumData->{'path'} ) ) {
		$dbh->do( q(DELETE FROM tracks WHERE parent_oid=?), {}, $oid );
		$dbh->do( q( DELETE FROM gme_library WHERE oid=? ), {}, $oid );
	}
	return $oid;
}

sub cleanupAlbum {
	my ( $oid, $httpd, $dbh ) = @_;
	my $albumData = $dbh->selectrow_hashref(
		q(SELECT path,picture_filename FROM gme_library WHERE oid=?),
		{}, $oid );
	my $query = q(SELECT filename FROM tracks WHERE parent_oid=? ORDER BY track);
	my @file_list =
		map { @$_ } @{ $dbh->selectall_arrayref( $query, {}, $oid ) };
	my $data = { 'filename' => undef };
	if ( clearAlbum( $albumData->{'path'}, \@file_list ) ) {
		updateTableEntry( 'tracks', 'parent_oid=?', [$oid], $data, $dbh );
	}
	return $oid;
}

1;
